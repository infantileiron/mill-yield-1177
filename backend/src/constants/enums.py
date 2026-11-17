from enum import Enum
class Role(str,Enum):
    admin="admin"
    analyst="analyst"
    viewer="viewer"
    external="external"
class ReviewStatus(str,Enum):
    queued="queued"
    running="running"
    completed="completed"
    approved="approved"
    failed="failed"
class BlindOrderStatus(str,Enum):
    sealed="sealed"
    unblinded="unblinded"
class BlindItemStatus(str,Enum):
    pending="pending"
    filled="filled"
    conflict="conflict"
LINES=["一线","二线","三线"]
