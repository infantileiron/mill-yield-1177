/** @typedef {{id:number,code:string,line:string,supplier:string,tonnes:number,received_date:string,samples:number}} Batch */
/** @typedef {{sample_code:string,batch_id:number,flour_yield:number,moisture:number,inspector:string}} Inspection */
/** @typedef {{id:number,title:string,line:string,status:string,result:object,note:string}} Review */
/** @typedef {{id:number,title:string,status:'sealed'|'unblinded',tolerance:number,created_by:string,unblinded_by:string,result:object,items:BlindItem[],summary:{total:number,pending:number,filled:number,conflict:number}}} BlindOrder */
/** @typedef {{id?:number,anon_code:string,status:'pending'|'filled'|'conflict',retest_yield:number|null,external_email?:string,sample_code?:string,batch_code?:string,original_yield?:number,diff?:number,submissions?:{value:number,kind:string,by:string,at:string}[]}} BlindItem */
export const API_VERSION='1';
