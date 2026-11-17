import {table} from '../components/common/table.js';
import {esc,fmt} from '../utils/format.js';
import {blindStatuses,blindItemStatuses} from '../constants/enums.js';
const orderBadge=s=>`<span class="badge ${esc(s)}">${esc(blindStatuses[s]||s)}</span>`;
const itemBadge=s=>`<span class="badge ${esc(s)}">${esc(blindItemStatuses[s]||s)}</span>`;
const at=t=>esc((t||'').slice(0,16).replace('T',' '));
function createForm(s){
 if(s.user.role!=='admin')return '';
 return `<h2>生成盲样送检单</h2><form id="blind-form"><label>送检标题<input name="title" required minlength="2" maxlength="120" value="11月17日盲样复测送检"></label><label>限差 ±（个百分点）<input name="tolerance" type="number" required min="0.1" max="10" step="0.1" value="0.5"></label><div class="picker">${s.inspections.slice(0,40).map(i=>`<div class="pick-row"><label class="pick-check"><input type="checkbox" name="pick" value="${i.id}"><span><strong>${esc(i.sample_code)}</strong><small>${esc(i.batch_code)} · ${esc(i.line)} · 原测 ${fmt(i.flour_yield)}%</small></span></label><select name="ext_${i.id}">${s.externals.map(x=>`<option>${esc(x)}</option>`).join('')}</select></div>`).join('')}</div><button class="primary" type="submit">冻结原值并分配匿名码 →</button></form><p class="hint">至少选择 2 条原检验。创建后原测出粉率与限差冻结；揭盲前查询与导出仅显示匿名码，外检账号仅见分配给自己的匿名码。</p>`;
}
function orderList(s){
 return `<h3>送检单</h3><div class="review-list">${s.blindOrders.map(o=>`<button class="review-choice" data-blind="${o.id}"><strong>${esc(o.title)}</strong><small>#${o.id} · 限差 ±${fmt(o.tolerance,1)} · 回填 ${o.summary.filled}/${o.summary.total}${o.summary.conflict?` · 冲突 ${o.summary.conflict}`:''}${o.summary.pending?` · 缺样 ${o.summary.pending}`:''}</small>${orderBadge(o.status)}</button>`).join('')||'<div class="empty">暂无送检单。</div>'}</div>`;
}
function submissionLog(i){
 if(!i.submissions?.length)return '—';
 return `<small>${i.submissions.map(x=>`${fmt(x.value)}% · ${esc(x.by)}${x.kind==='adjudicated'?'（裁定）':x.kind==='conflict'?'（异值）':''}`).join('<br>')}</small>`;
}
function sealedStaff(s,o){
 const canUnblind=o.summary.pending===0&&o.summary.conflict===0&&o.summary.total>=2;
 return `<div class="section-head"><h2>${esc(o.title)}</h2>${orderBadge(o.status)}</div><p>限差 ±${fmt(o.tolerance,1)} 个百分点 · 创建人 ${esc(o.created_by)} · ${at(o.created_at)} UTC</p><div class="report-note"><strong>盲态封存中：批号与原测值已隐藏。</strong><p>外检账号仅见分配的匿名码并回填出粉率；缺样或异值冲突未清时不能揭盲，揭盲失败仍保持封存。</p></div>${table(['匿名码','状态','复测值','外检账号','留痕 / 裁定'],o.items.map(i=>[`<strong>${esc(i.anon_code)}</strong>`,itemBadge(i.status),i.retest_yield==null?'—':fmt(i.retest_yield)+'%',esc(i.external_email),i.status==='conflict'&&s.user.role==='admin'?`<form class="inline-form" data-adjudicate="${i.id}" data-order="${o.id}"><input name="flour_yield" type="number" min="0.01" max="100" step="0.01" required placeholder="裁定值 %"><button class="mini" type="submit">裁定采用</button></form>${submissionLog(i)}`:submissionLog(i)]))}<button class="primary" id="unblind" data-id="${o.id}" ${s.user.role==='admin'&&canUnblind?'':'disabled'}>揭盲并计算配对统计</button>${canUnblind?'<p class="hint">全部盲样已回填且无冲突，可以揭盲。揭盲后按匿名码配对，计算复测减原测的均值、样本标准差与超差清单。</p>':`<p class="hint">${o.summary.pending?`缺样 ${o.summary.pending} 个；`:''}${o.summary.conflict?`未裁定冲突 ${o.summary.conflict} 个；`:''}清点完成后才能揭盲。</p>`}<button class="outline" id="blind-download" data-id="${o.id}">下载盲态 CSV（隐去批号与原值） ↓</button>`;
}
function unblindedStaff(s,o){
 const r=o.result;
 return `<div class="section-head"><h2>${esc(o.title)}</h2>${orderBadge(o.status)}</div><p>揭盲人 ${esc(o.unblinded_by)} · ${at(o.unblinded_at)} UTC · 限差 ±${fmt(r.tolerance,1)}（送检时冻结，依据固定）</p><div class="metrics"><div><small>配对样本</small><b>${r.n}</b></div><div><small>差值均值</small><b>${fmt(r.mean)}<em>pp</em></b></div><div><small>样本标准差</small><b>${fmt(r.std)}<em>pp</em></b></div><div><small>超差样本</small><b class="rust">${r.over.length}</b></div></div><div class="formula">差值 = 复测 − 原测 · 均值 ${fmt(r.mean)} pp · 样本标准差（n−1）${fmt(r.std)} pp<br>超差判定：|差值| 严格大于限差 ±${fmt(r.tolerance,1)} pp，边界保留。</div>${r.over.length?`<div class="report-note"><strong>超差清单 ${r.over.length} 条。</strong><p>以下配对差值超出冻结限差，请安排批次处理并在复核意见中说明。</p></div>${table(['匿名码','样本编号','批次','原测','复测','差值'],r.over.map(x=>[esc(x.anon_code),esc(x.sample_code),esc(x.batch_code),fmt(x.original_yield)+'%',fmt(x.retest_yield)+'%',`<span class="rust">${fmt(x.diff)}</span>`]))}`:'<div class="report-note"><strong>全部配对均在限差内。</strong></div>'}<h3>完整配对</h3>${table(['匿名码','样本编号','批次','原测','复测','差值','超差'],r.pairs.map(x=>[esc(x.anon_code),esc(x.sample_code),esc(x.batch_code),fmt(x.original_yield)+'%',fmt(x.retest_yield)+'%',fmt(x.diff),Math.abs(x.diff)>r.tolerance?'<span class="rust">是</span>':'否']))}<button class="outline" id="blind-download" data-id="${o.id}">下载完整配对 CSV ↓</button><p class="checksum">SHA-256 ${esc(r.checksum)}</p>`;
}
function externalView(s,o){
 if(o.status==='unblinded')return `<div class="section-head"><h2>${esc(o.title)}</h2>${orderBadge(o.status)}</div><p>该送检单已揭盲，以下为分配给当前账号的匿名码配对结果。</p>${table(['匿名码','样本编号','批次','原测','复测','差值'],o.items.map(i=>[esc(i.anon_code),esc(i.sample_code),esc(i.batch_code),fmt(i.original_yield)+'%',fmt(i.retest_yield)+'%',fmt(i.diff)]))}<button class="outline" id="blind-download" data-id="${o.id}">下载配对 CSV ↓</button>`;
 return `<div class="section-head"><h2>${esc(o.title)}</h2>${orderBadge(o.status)}</div><p>限差 ±${fmt(o.tolerance,1)} 个百分点 · 仅显示分配给当前账号的匿名码；批号与原测值揭盲前不可见。</p>${table(['匿名码','状态','回填出粉率'],o.items.map(i=>{
  if(i.status==='pending')return [`<strong>${esc(i.anon_code)}</strong>`,itemBadge(i.status),`<form class="inline-form" data-backfill="${esc(i.anon_code)}" data-order="${o.id}"><input name="flour_yield" type="number" min="0.01" max="100" step="0.01" required placeholder="出粉率 %"><button class="mini" type="submit">回填</button></form>`];
  if(i.status==='filled')return [`<strong>${esc(i.anon_code)}</strong>`,itemBadge(i.status),`已回填 ${fmt(i.retest_yield)}%<small>同码同值重试不重复记录；异值将登记冲突</small>`];
  return [`<strong>${esc(i.anon_code)}</strong>`,itemBadge(i.status),`已登记 ${fmt(i.retest_yield)}%<small>存在异值，待负责人裁定</small>`];
 }))}<button class="outline" id="blind-download" data-id="${o.id}">下载盲态 CSV ↓</button>`;
}
function detail(s,o){
 if(s.user.role==='external')return externalView(s,o);
 return o.status==='unblinded'?unblindedStaff(s,o):sealedStaff(s,o);
}
export function blindPage(s){
 const o=s.blindSelected||s.blindOrders[0];
 return `<header><p class="eyebrow">05 / BLIND RETEST</p><h1>盲样比对</h1><p>外送复测与原始检验解耦：匿名码送检、同值幂等回填、异值裁定、齐样后揭盲配对。复测数据不进入分布诊断。</p></header><div class="workspace"><section class="paper">${createForm(s)}${orderList(s)}</section><section>${o?detail(s,o):'<div class="empty">暂无送检单。负责人从左侧选择至少 2 条原检验生成送检单。</div>'}</section></div>`;
}
