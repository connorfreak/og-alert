# 1. Import library yang dibutuhkan
import os
import ccxt
import pandas as pd
from datetime import datetime
from gtts import gTTS
import io
from telegram import Bot

# 2. Ambil token & chat_id dari GitHub Secrets (rahasia)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# 3. Setting coin & timeframe (cuma OGUSDT 1H)
SYMBOL = "OGUSDT"
TIMEFRAME = "1h"
EMA_PERIOD = 21

# 4. Hubungkan ke Bybit Futures
bybit = ccxt.bybit({
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})


# 5. Fungsi utama cek EMA-21
def cek_ogusdt():
    try:
        # Ambil data 50 candle 1H terakhir
        ohlcv = bybit.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=50)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Hitung EMA-21
        df['ema21'] = df['close'].ewm(span=EMA_PERIOD, adjust=False).mean()
        
        # Data candle sekarang & sebelumnya
        harga_sekarang = df['close'].iloc[-1]
        ema21_sekarang = df['ema21'].iloc[-1]
        harga_sebelum = df['close'].iloc[-2]
        ema21_sebelum = df['ema21'].iloc[-2]
        high = df['high'].iloc[-1]
        low = df['low'].iloc[-1]
        
        # Waktu candle (contoh: 2025-12-05 14:00)
        waktu_candle = datetime.fromtimestamp(df['timestamp'].iloc[-1]/1000).strftime("%Y-%m-%d %H:00")
        
        # Anti-spam: cek apakah sudah kirim di candle ini
        file_flag = f"/tmp/og_{waktu_candle}.flag"
        if os.path.exists(file_flag):
            print("Sudah kirim alert di candle ini")
            return
        
        # Deteksi cross atau sentuh EMA-21
        naik_cross = harga_sebelum <= ema21_sebelum and harga_sekarang > ema21_sekarang
        turun_cross = harga_sebelum >= ema21_sebelum and harga_sekarang < ema21_sekarang
        sentuh_bawah = low <= ema21_sekarang <= high and harga_sekarang > ema21_sekarang
        sentuh_atas = high >= ema21_sekarang >= low and harga_sekarang < ema21_sekarang
        
        if naik_cross or turun_cross or sentuh_bawah or sentuh_atas:
            arah = "NAIK MELEWATI" if (naik_cross or sentuh_bawah) else "TURUN MENYENTUH"
            
            # Teks pesan
            pesan = f"OGUSDT (Fartcoin)\n" \
                    f"{arah} EMA-21 (1H)\n" \
                    f"Harga: ${harga_sekarang:.6f}\n" \
                    f"EMA-21: ${ema21_sekarang:.6f}\n" \
                    f"{waktu_candle} UTC"
            
            # Voice bahasa Indonesia
            suara = f"Peringatan! OGUSDT harga {arah.lower()} EMA dua puluh satu. " \
                    f"Harga sekarang {harga_sekarang:.5f} dolar."
            tts = gTTS(text=suara, lang='id', slow=False)
            buffer = io.BytesIO()
            tts.write_to_fp(buffer)
            buffer.seek(0)
            
            # Kirim ke Telegram
            bot = Bot(token=TELEGRAM_TOKEN)
            bot.send_message(chat_id=CHAT_ID, text=pesan)
            bot.send_voice(chat_id=CHAT_ID, voice=buffer, filename="og_alert.mp3")
            
            # Buat flag supaya tidak kirim lagi di candle ini
            with open(file_flag, 'w') as f:
                f.write("sent")
                
            print(f"[ALERT] OGUSDT {arah} EMA-21 → {waktu_candle}")
            
    except Exception as e:
        print(f"Error: {e}")

# TES LANGSUNG KIRIM PESAN (hapus lagi nanti kalau sudah berhasil)
bot = Bot(token=TELEGRAM_TOKEN)
bot.send_message(chat_id=CHAT_ID, text="Bot OGUSDT sudah NYALA! Tes sukses ✅")
# Jalankan fungsi
cek_ogusdt()
print("Cek OGUSDT selesai")
