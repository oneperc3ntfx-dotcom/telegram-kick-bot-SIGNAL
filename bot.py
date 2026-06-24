import os
import requests

from datetime import datetime, timedelta
from dotenv import load_dotenv

from telegram.ext import (
    Application
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
TOPIC_ID = int(os.getenv("TOPIC_ID"))
SHEET_URL = os.getenv("SHEET_URL")

warned_10 = set()
warned_5 = set()
kicked = set()


def get_members():

    try:

        r = requests.get(
            SHEET_URL,
            timeout=30
        )

        data = r.json()

        return data.get("data", [])

    except Exception as e:

        print(e)

        return []


async def send_warning(
    bot,
    user_id,
    username,
    minutes_left
):

    text = f"""
⚠️ Pemberitahuan Keanggotaan

Yth. <a href="tg://user?id={user_id}">{username}</a>,

Berdasarkan data administrasi terbaru, akun Anda dijadwalkan untuk dikeluarkan dari grup dalam waktu {minutes_left} menit sejak pemberitahuan ini dikirimkan.

Apabila Anda masih ingin mempertahankan akses ke grup atau terdapat kekeliruan pada data keanggotaan Anda, mohon segera melakukan konfirmasi sebelum batas waktu berakhir.

Untuk melakukan upgrade atau perpanjangan langganan, silakan klik tautan berikut:

👉 https://t.me/AITOOLSIGNAL_BOT?start=upgrade

Atau hubungi:

👉 @AITOOLSIGNAL_BOT

Jika tidak ada tindakan atau konfirmasi hingga batas waktu yang ditentukan, sistem akan secara otomatis mengeluarkan akun Anda dari grup.

Terima kasih atas perhatian dan kerja samanya.
"""

    await bot.send_message(
        chat_id=GROUP_ID,
        message_thread_id=TOPIC_ID,
        text=text,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


async def kick_member(
    bot,
    user_id,
    username
):

    try:

        await bot.send_message(
            chat_id=GROUP_ID,
            message_thread_id=TOPIC_ID,
            text=(
                f"🔴 Masa aktif {username} telah berakhir.\n\n"
                f"Sistem melakukan pengeluaran akun secara otomatis."
            )
        )

        await bot.ban_chat_member(
            GROUP_ID,
            user_id
        )

        await bot.unban_chat_member(
            GROUP_ID,
            user_id
        )

        print(
            f"KICKED {username}"
        )

    except Exception as e:

        print(
            f"ERROR KICK {username}: {e}"
        )


async def checker(context):

    members = get_members()

    now = datetime.utcnow()

    for member in members:

        try:

            username = member["username"]
            user_id = int(member["userId"])

            kick_date = datetime.fromisoformat(
                member["kickDate"].replace(
                    "Z",
                    "+00:00"
                )
            )

            kick_date = kick_date.replace(
                tzinfo=None
            )

            warn_10 = kick_date - timedelta(
                minutes=10
            )

            warn_5 = kick_date - timedelta(
                minutes=5
            )

            if (
                now >= warn_10
                and now < warn_5
                and user_id not in warned_10
            ):

                warned_10.add(user_id)

                await send_warning(
                    context.bot,
                    user_id,
                    username,
                    10
                )

                print(
                    f"10 MIN WARNING {username}"
                )

            if (
                now >= warn_5
                and now < kick_date
                and user_id not in warned_5
            ):

                warned_5.add(user_id)

                await send_warning(
                    context.bot,
                    user_id,
                    username,
                    5
                )

                print(
                    f"5 MIN WARNING {username}"
                )

            if (
                now >= kick_date
                and user_id not in kicked
            ):

                kicked.add(
                    user_id
                )

                await kick_member(
                    context.bot,
                    user_id,
                    username
                )

        except Exception as e:

            print(
                f"ROW ERROR: {e}"
            )


def main():

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.job_queue.run_repeating(
        checker,
        interval=60,
        first=10
    )

    print(
        "BOT RUNNING..."
    )

    app.run_polling()


if __name__ == "__main__":
    main()
