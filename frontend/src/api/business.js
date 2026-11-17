import {api,post,download,downloadFile} from './client.js';
export const batches={list:()=>api('/batches'),create:d=>post('/batches',d)};
export const inspections={list:()=>api('/inspections'),create:d=>post('/inspections',d)};
export const reviews={list:()=>api('/reviews'),get:id=>api('/reviews/'+id),create:d=>post('/reviews',d),approve:(id,note)=>post(`/reviews/${id}/approve`,{note}),download};
export const blind={
 list:()=>api('/blind/orders'),
 get:id=>api('/blind/orders/'+id),
 externals:()=>api('/blind/externals'),
 create:d=>post('/blind/orders',d),
 backfill:(id,d)=>post(`/blind/orders/${id}/backfill`,d),
 adjudicate:(id,d)=>post(`/blind/orders/${id}/adjudicate`,d),
 unblind:id=>post(`/blind/orders/${id}/unblind`,{}),
 download:id=>downloadFile(`/blind/orders/${id}/export`,`mill-blind-${id}.csv`)
};
