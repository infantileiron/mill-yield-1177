import csv,io
from fastapi import HTTPException
from fastapi.responses import Response
def export_review(obj):
    if obj.status not in ('completed','approved'):raise HTTPException(409,'计算完成后才可导出')
    output=io.StringIO();w=csv.writer(output)
    w.writerow(['复核单',obj.id,'标题',obj.title,'状态',obj.status,'范围',obj.line])
    for k in ['n','mean','std','q1','median','q3','iqr','lower','upper','checksum']:w.writerow([k,obj.result[k]])
    w.writerow(['签核人',obj.approved_by,'签核意见',obj.note])
    w.writerow(['样本编号','批次','产线','出粉率','水分','异常'])
    out={r['sample_code'] for r in obj.result['outliers']}
    for row in obj.snapshot:w.writerow([row['sample_code'],row['batch_code'],row['line'],row['flour_yield'],row['moisture'],'是' if row['sample_code'] in out else '否'])
    return Response('﻿'+output.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="mill-yield-review-{obj.id}.csv"'})
def export_blind(order,items,staff_view):
    reveal=order.status=='unblinded'
    output=io.StringIO();w=csv.writer(output)
    w.writerow(['盲样送检单',order.id,'标题',order.title,'状态',order.status,'限差',order.tolerance])
    w.writerow(['创建人',order.created_by,'揭盲人',order.unblinded_by or '—'])
    if reveal and staff_view and order.result:
        r=order.result
        for k in ['n','mean','std','tolerance','checksum']:w.writerow([k,r[k]])
        w.writerow(['超差数',len(r['over'])])
    if reveal:
        w.writerow(['匿名码','样本编号','批次','原测出粉率','复测出粉率','差值','超差'])
        for i in items:
            diff=round(i.retest_yield-i.original_yield,4)
            w.writerow([i.anon_code,i.sample_code,i.batch_code,i.original_yield,i.retest_yield,diff,'是' if abs(diff)>order.tolerance else '否'])
    else:
        w.writerow(['匿名码','状态','复测出粉率']+(['外检账号'] if staff_view else []))
        for i in items:
            row=[i.anon_code,i.status,i.retest_yield if i.retest_yield is not None else '']
            if staff_view:row.append(i.external_email)
            w.writerow(row)
    return Response('﻿'+output.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="mill-blind-{order.id}.csv"'})
