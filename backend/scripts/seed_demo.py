import random
from datetime import datetime,timezone
from sqlalchemy import select,func
from src.config.database import Session,Base,engine
from src.models.entities import User,Batch,Inspection,Review,BlindOrder,BlindItem,BlindBackfill
from src.utils.security import password_hash
from src.services.statistics import diagnose,blind_stats
def seed():
    Base.metadata.create_all(engine);rng=random.Random(3101)
    with Session() as db:
        for email,role in [('admin@demo.local','admin'),('analyst@demo.local','analyst'),('viewer@demo.local','viewer'),('ext1@demo.local','external'),('ext2@demo.local','external')]:
            if not db.scalar(select(User).where(User.email==email)):db.add(User(email=email,password_hash=password_hash('Demo123!'),role=role))
        db.flush()
        for i in range(40):
            code='QH-1115-A' if i==0 else f'QH-{1101+i:04}-B'
            batch=db.scalar(select(Batch).where(Batch.code==code))
            if not batch:
                batch=Batch(code=code,line=['一线','二线','三线'][i%3],supplier=['丰垦粮业','北原合作社','河谷粮仓'][i%3],tonnes=round(25+i*.7,1),received_date=f'2026-11-{1+i%15:02}')
                db.add(batch);db.flush()
            for j in range(15):
                sc=f'{code}-S{j+1:02}';val=round(max(65,min(82,rng.gauss(73+i%3*1.4,1.6))),2)
                if i in (0,9,25) and j==14:val=65.0 if i==0 else 82.0
                moisture=round(rng.uniform(11.5,14.2),2)
                if not db.scalar(select(Inspection).where(Inspection.sample_code==sc)):
                    db.add(Inspection(sample_code=sc,batch_id=batch.id,flour_yield=val,moisture=moisture,inspector=['林洁','周麦','陈禾'][i%3]))
        db.flush()
        if not db.scalar(select(Review).where(Review.title=='11月15日全线出粉率初审')):
            from src.services.business import inspections
            rows=inspections(db)
            db.add(Review(title='11月15日全线出粉率初审',line='全部',status='completed',snapshot=rows,result=diagnose(rows),created_by='analyst@demo.local',note='待质量负责人核对异常点及签核'))
        first=db.scalar(select(Batch).where(Batch.code=='QH-1115-A'))
        samples={x.sample_code:x for x in db.scalars(select(Inspection).where(Inspection.batch_id==first.id))}
        if not db.scalar(select(BlindOrder).where(BlindOrder.title=='11月15日盲样复测送检')):
            order=BlindOrder(title='11月15日盲样复测送检',tolerance=0.5,created_by='admin@demo.local')
            db.add(order);db.flush()
            plan=[('S01','BM-K7Q2XA',0.18,'ext1@demo.local'),('S02','BM-M3V8PD',-0.27,'ext1@demo.local'),('S03','BM-R9T4HZ',0.64,'ext2@demo.local')]
            pairs=[]
            for suffix,anon,delta,ext in plan:
                src=samples[f'QH-1115-A-{suffix}'];retest=round(src.flour_yield+delta,2)
                item=BlindItem(order_id=order.id,anon_code=anon,inspection_id=src.id,sample_code=src.sample_code,batch_code='QH-1115-A',original_yield=src.flour_yield,external_email=ext,retest_yield=retest,status='filled')
                db.add(item);db.flush()
                db.add(BlindBackfill(item_id=item.id,value=retest,kind='accepted',submitted_by=ext))
                pairs.append({'anon_code':anon,'sample_code':src.sample_code,'batch_code':'QH-1115-A','original_yield':src.flour_yield,'retest_yield':retest})
            order.result=blind_stats(pairs,0.5);order.status='unblinded';order.unblinded_by='admin@demo.local';order.unblinded_at=datetime.now(timezone.utc)
        if not db.scalar(select(BlindOrder).where(BlindOrder.title=='11月16日盲样复测送检')):
            order=BlindOrder(title='11月16日盲样复测送检',tolerance=0.5,created_by='admin@demo.local')
            db.add(order);db.flush()
            plan=[('S04','BM-W2E6RT','ext1@demo.local',0.21),('S05','BM-Y8U3IK','ext1@demo.local',None),('S06','BM-P5L9NB','ext2@demo.local',None)]
            for suffix,anon,ext,delta in plan:
                src=samples[f'QH-1115-A-{suffix}']
                item=BlindItem(order_id=order.id,anon_code=anon,inspection_id=src.id,sample_code=src.sample_code,batch_code='QH-1115-A',original_yield=src.flour_yield,external_email=ext)
                if delta is not None:
                    item.retest_yield=round(src.flour_yield+delta,2);item.status='filled'
                    db.add(item);db.flush()
                    db.add(BlindBackfill(item_id=item.id,value=item.retest_yield,kind='accepted',submitted_by=ext))
                else:db.add(item)
        db.commit()
        print({m.__tablename__:db.scalar(select(func.count()).select_from(m)) for m in [Batch,Inspection,Review,BlindOrder,BlindItem]})
if __name__=='__main__':seed()
