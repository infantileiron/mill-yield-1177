import secrets
from datetime import datetime,timezone
from sqlalchemy import select
from fastapi import HTTPException
from src.models.entities import BlindOrder,BlindItem,BlindBackfill,Inspection,Batch,User
from src.services.statistics import blind_stats
from src.utils.serialize import record
ALPHABET='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
def externals(db):
    return [u.email for u in db.scalars(select(User).where(User.role=='external').order_by(User.email))]
def _items(db,order_id):
    return db.scalars(select(BlindItem).where(BlindItem.order_id==order_id).order_by(BlindItem.id)).all()
def _summary(items):
    return {'total':len(items),'pending':sum(1 for i in items if i.status=='pending'),'filled':sum(1 for i in items if i.status=='filled'),'conflict':sum(1 for i in items if i.status=='conflict')}
def _submissions(db,item_ids):
    if not item_ids:return {}
    out={}
    for r in db.scalars(select(BlindBackfill).where(BlindBackfill.item_id.in_(item_ids)).order_by(BlindBackfill.id)):
        out.setdefault(r.item_id,[]).append({'value':r.value,'kind':r.kind,'by':r.submitted_by,'at':r.created_at.isoformat()})
    return out
def _item_view(item,reveal,staff,submissions=None):
    v={'anon_code':item.anon_code,'status':item.status,'retest_yield':item.retest_yield}
    if staff:
        v['id']=item.id;v['external_email']=item.external_email;v['submissions']=submissions or []
    if reveal:
        v.update(sample_code=item.sample_code,batch_code=item.batch_code,original_yield=item.original_yield,diff=round(item.retest_yield-item.original_yield,4) if item.retest_yield is not None else None)
    return v
def _view(db,order,items,user):
    staff=user.role!='external'
    reveal=order.status=='unblinded'
    subs=_submissions(db,[i.id for i in items]) if staff else {}
    out={k:v for k,v in record(order).items() if k!='result'}
    out['result']=order.result if (reveal and staff) else {}
    out['items']=[_item_view(i,reveal,staff,subs.get(i.id,[])) for i in items]
    out['summary']=_summary(items)
    return out
def _scoped(db,order,user):
    items=_items(db,order.id)
    if user.role=='external':
        items=[i for i in items if i.external_email==user.email]
        if not items:raise HTTPException(404,'送检单不存在或未分配给当前账号')
    return items
def orders(db,user):
    out=[]
    for o in db.scalars(select(BlindOrder).order_by(BlindOrder.id.desc())):
        items=_items(db,o.id)
        if user.role=='external':
            items=[i for i in items if i.external_email==user.email]
            if not items:continue
        out.append(_view(db,o,items,user))
    return out
def detail(db,id,user):
    order=db.get(BlindOrder,id)
    if not order:raise HTTPException(404,'送检单不存在')
    return _view(db,order,_scoped(db,order,user),user)
def create_order(db,data,user):
    ids=[x['inspection_id'] for x in data['items']]
    if len(set(ids))!=len(ids):raise HTTPException(422,'同一检验记录只能在送检单中出现一次')
    found={i.id:(i,code) for i,code in db.execute(select(Inspection,Batch.code).join(Batch,Batch.id==Inspection.batch_id).where(Inspection.id.in_(ids)))}
    missing=[i for i in ids if i not in found]
    if missing:raise HTTPException(404,f'检验记录不存在：{missing}')
    valid=set(externals(db))
    for x in data['items']:
        if x['external_email'] not in valid:raise HTTPException(422,f"外检账号不存在：{x['external_email']}")
    codes=set()
    while len(codes)<len(ids):codes.add('BM-'+''.join(secrets.choice(ALPHABET) for _ in range(6)))
    order=BlindOrder(title=data['title'],tolerance=data['tolerance'],created_by=user.email)
    db.add(order);db.flush()
    for x,anon in zip(data['items'],codes):
        ins,batch_code=found[x['inspection_id']]
        db.add(BlindItem(order_id=order.id,anon_code=anon,inspection_id=ins.id,sample_code=ins.sample_code,batch_code=batch_code,original_yield=ins.flour_yield,external_email=x['external_email']))
    db.commit()
    return detail(db,order.id,user)
def _locked_order(db,id):
    order=db.scalar(select(BlindOrder).where(BlindOrder.id==id).with_for_update())
    if not order:raise HTTPException(404,'送检单不存在')
    return order
def backfill(db,id,data,user):
    order=_locked_order(db,id)
    if order.status!='sealed':raise HTTPException(409,'送检单已揭盲，停止回填')
    item=db.scalar(select(BlindItem).where(BlindItem.order_id==id,BlindItem.anon_code==data['anon_code']))
    if not item or item.external_email!=user.email:raise HTTPException(404,'匿名码不存在或未分配给当前账号')
    value=data['flour_yield']
    if item.retest_yield is not None and abs(item.retest_yield-value)<1e-9:
        db.commit()
        return {'anon_code':item.anon_code,'status':item.status,'idempotent':True}
    if item.retest_yield is not None:
        item.status='conflict'
        db.add(BlindBackfill(item_id=item.id,value=value,kind='conflict',submitted_by=user.email))
        db.commit()
        raise HTTPException(409,'与已回填值不一致，已登记异值冲突，待负责人裁定')
    item.retest_yield=value;item.status='filled'
    db.add(BlindBackfill(item_id=item.id,value=value,kind='accepted',submitted_by=user.email))
    db.commit()
    return {'anon_code':item.anon_code,'status':'filled','idempotent':False}
def adjudicate(db,id,data,user):
    order=_locked_order(db,id)
    if order.status!='sealed':raise HTTPException(409,'送检单已揭盲，无法裁定')
    item=db.get(BlindItem,data['item_id'])
    if not item or item.order_id!=id:raise HTTPException(404,'盲样条目不存在')
    if item.status!='conflict':raise HTTPException(409,'该盲样无异值冲突，无需裁定')
    item.retest_yield=data['flour_yield'];item.status='filled'
    db.add(BlindBackfill(item_id=item.id,value=data['flour_yield'],kind='adjudicated',submitted_by=user.email))
    db.commit()
    return detail(db,id,user)
def unblind(db,id,user):
    order=_locked_order(db,id)
    if order.status=='unblinded':raise HTTPException(409,'送检单已揭盲，请勿重复操作')
    items=_items(db,id)
    missing=[i.anon_code for i in items if i.status=='pending']
    if missing:raise HTTPException(409,f"尚有 {len(missing)} 个盲样缺回填（{'、'.join(missing)}），不能揭盲")
    conflicts=[i.anon_code for i in items if i.status=='conflict']
    if conflicts:raise HTTPException(409,f"存在未裁定的异值冲突（{'、'.join(conflicts)}），不能揭盲")
    pairs=[{'anon_code':i.anon_code,'sample_code':i.sample_code,'batch_code':i.batch_code,'original_yield':i.original_yield,'retest_yield':i.retest_yield} for i in items]
    order.result=blind_stats(pairs,order.tolerance)
    order.status='unblinded';order.unblinded_by=user.email;order.unblinded_at=datetime.now(timezone.utc)
    db.commit()
    return detail(db,id,user)
def export_rows(db,id,user):
    order=db.get(BlindOrder,id)
    if not order:raise HTTPException(404,'送检单不存在')
    return order,_scoped(db,order,user)
