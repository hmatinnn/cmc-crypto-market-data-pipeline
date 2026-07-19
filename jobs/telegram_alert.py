# import requests
# import os

# TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
# TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


# def send_telegram_message(message: str):
#     url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
#     payload = {
#         "chat_id": TELEGRAM_CHAT_ID,
#         "text": message
#        ## "parse_mode": "Markdown"
#     }
#     response = requests.post(url, json=payload)
#     response.raise_for_status()


# def send_dag_failure_alert(context):
#     dag_id = context["dag"].dag_id
#     task_id = context["task_instance"].task_id
#     log_url = context["task_instance"].log_url
#     exception = context.get("exception")

#     try:
#         logical_date = context.get("logical_date")
#     except KeyError:
#         logical_date = None
#     if not logical_date:
#         logical_date = "N/A"

#     message = (
#         f"*DAG FAIL*\n"
#         f"*DAG:* `{dag_id}`\n"
#         f"*Task:* `{task_id}`\n"
#         f"*Time:* `{logical_date}`\n"
#         f"*Error:* `{str(exception)[:300]}`\n"
#         f"[View Logs]({log_url})"
#     )
#     try:
#         send_telegram_message(message)
#     except Exception as e:
#         print(f"Telegram alert did not send: {e}")


# def send_soda_alert(scan):
#     if not scan.has_checks_warn_or_fail():
#         return

#     failed_checks = scan.get_checks_warn_or_fail()

#     grouped = {}
#     for c in failed_checks:
#         table = getattr(c, "table", None) or "unknown_table"
#         grouped.setdefault(table, []).append(c.name)

#     lines = ["*SODA DQ ALERT*"]
#     for table, checks in grouped.items():
#         lines.append(f"\n*Table:* `{table}`")
#         for check_name in checks:
#             lines.append(f"  - {check_name}")

#     message = "\n".join(lines)
#     try:
#         send_telegram_message(message)
#     except Exception as e:
#         print(f"Telegram alert did not send: {e}")




import os
import requests

# Telegram credentials
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram_message(message: str):
    """Telegram-a mesaj göndərən ana funksiya (Markdown dəstəyi ilə)"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",  
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()


def _extract_table_name(check) -> str:
    """
    Soda Check obyektinin partition.table iyerarxiyasından 
    cədvəlin real adını təhlükəsiz şəkildə çıxarır.
    """
    partition = getattr(check, "partition", None)
    if partition:
        table_obj = getattr(partition, "table", None)
        if table_obj:
            for attr in ["table_name", "dataset_name", "name"]:
                val = getattr(table_obj, attr, None)
                if val:
                    return str(val)
            return str(table_obj)
            
    dataset = getattr(check, "dataset", None)
    if dataset:
        return getattr(dataset, "dataset_name", str(dataset))

    cfg = getattr(check, "check_cfg", None)
    if cfg:
        val = getattr(cfg, "dataset_name", None) or getattr(cfg, "table_name", None)
        if val:
            return str(val)

    return "unknown_table"


def send_dag_failure_alert(context):
    dag_id = context["dag"].dag_id
    task_id = context["task_instance"].task_id
    log_url = context["task_instance"].log_url
    exception = context.get("exception")

    try:
        logical_date = context.get("logical_date")
    except KeyError:
        logical_date = None
    if not logical_date:
        logical_date = "N/A"

    message = (
        f"*DAG FAIL*\n"
        f"*DAG:* `{dag_id}`\n"
        f"*Task:* `{task_id}`\n"
        f"*Time:* `{logical_date}`\n"
        f"*Error:* `{str(exception)[:300]}`\n"
        f"[View Logs]({log_url})"
    )
    try:
        send_telegram_message(message)
    except Exception as e:
        print(f"Telegram alert did not send: {e}")


def send_soda_alert(scan):
    """Soda DQ xətalarını qruplaşdırıb Telegram-a göndərir"""
    if not scan.has_checks_warn_or_fail():
        return

    failed_checks = scan.get_checks_warn_or_fail()

    grouped = {}
    for c in failed_checks:
        table = _extract_table_name(c)
        grouped.setdefault(table, []).append(c.name)

    lines = ["*SODA DQ ALERT*"]
    for table, checks in grouped.items():
        lines.append(f"\n*Table:* `{table}`")
        for check_name in checks:
            lines.append(f"  - {check_name}")

    message = "\n".join(lines)
    try:
        send_telegram_message(message)
    except Exception as e:
        print(f"Telegram alert did not send: {e}")