import {batches,inspections,reviews,blind} from '../api/business.js';
export const state={user:null,batches:[],inspections:[],reviews:[],blindOrders:[],blindSelected:null,externals:[],selected:null};
export async function refresh(){
 if(state.user.role==='external'){state.blindOrders=await blind.list();}
 else{
  [state.batches,state.inspections,state.reviews,state.blindOrders]=await Promise.all([batches.list(),inspections.list(),reviews.list(),blind.list()]);
  if(state.user.role==='admin'&&!state.externals.length)state.externals=await blind.externals().catch(()=>[]);
 }
 if(state.selected)state.selected=await reviews.get(state.selected.id);
 if(state.blindSelected)state.blindSelected=state.blindOrders.find(o=>o.id===state.blindSelected.id)||null;
}
