from config import FORCE_SUBSCRIBE, FORCE_SUB_CHANNELS

def is_user_joined(bot, user_id: int) -> bool:
    """
    Returns True agar user ne saare compulsory channels join kar liye hain.
    """
    if not FORCE_SUBSCRIBE:
        return True

    for channel in FORCE_SUB_CHANNELS:
        try:
            member = bot.get_chat_member(channel["chat_id"], user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except Exception:
            # Agar bot channel me admin nahi hai ya koi error hai, toh access lock rakhega
            return False
    return True
