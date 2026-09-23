AUTO={"ALLOW_TRANSACTION","MONITOR_CARD","MONITOR_CONNECTED_CARDS","WARN_CUSTOMER","VERIFY_WITH_CUSTOMER","STEP_UP_AUTH","GENERATE_REPORT","CREATE_CASE","ESCALATE_TO_ANALYST","CLOSE_NO_FRAUD"}
def route(action, exposure):
    if action in AUTO:return "auto"
    if action=="DECLINE_TRANSACTION":return "L1"
    if action=="BLOCK_CARD":return "L1" if exposure<=2500 else "L2"
    return "L2"
def allowed(action, exposure=0):
    return {"action":action,"route":route(action,exposure)}
