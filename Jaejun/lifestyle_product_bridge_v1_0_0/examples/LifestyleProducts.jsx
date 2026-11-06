import React, { useMemo, useState } from 'react';
import { INTERESTS, buildInterestCards, listProducts } from '../src/bridge.js';

/** 기존 제품 확인/상담 절차가 완료된 경우에만 allowProductBrowsing=true 전달.
 * 서버 API/모델 수정 불필요. products에는 data/products.json의 배열을 전달.
 * 프로덕션에서 원문을 출력할 때도 dangerouslySetInnerHTML을 사용하지 말 것.
 */
export default function LifestyleProducts({ products, allowProductBrowsing = false,
  onOpenExistingSafetyFlow = () => {} }) {
  const [selected, setSelected] = useState([]);
  const [active, setActive] = useState(null);
  const [form, setForm] = useState('');
  const [pool, setPool] = useState('');
  const [maxDailyUnits, setMaxDailyUnits] = useState(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(12);
  const [eyeOmega, setEyeOmega] = useState(false);
  const cards = buildInterestCards(selected);
  const result = useMemo(() => active ? listProducts(products, {
    interestId: active, includeEyeOmega3: eyeOmega, form, pool,
    maxDailyUnits, search, page, pageSize,
  }) : null, [products, active, eyeOmega, form, pool, maxDailyUnits, search, page, pageSize]);
  function resetFilters() { setForm(''); setPool(''); setMaxDailyUnits(null); setSearch(''); setPage(1); setEyeOmega(false); }
  function toggle(id) {
    const next = selected.includes(id) ? selected.filter(x => x !== id) : [...selected, id];
    setSelected(next);
    if (!next.includes(active)) { setActive(next[0] ?? null); resetFilters(); }
  }
  return <section aria-label="관심 건강 정보">
    <h2>추가로 살펴보고 싶은 건강 정보를 골라 주세요</h2>
    <p>여러 항목을 선택하거나 선택하지 않고 넘어갈 수 있어요.</p>
    {INTERESTS.map(item => <label key={item.id} style={{ marginRight: 16 }}>
      <input type="checkbox" checked={selected.includes(item.id)} onChange={() => toggle(item.id)} />{item.label}
    </label>)}
    <button onClick={() => { setSelected([]); setActive(null); resetFilters(); }}>선택하지 않음</button>
    <p>관심 항목으로 살펴보는 제품 정보이며, 영양 부족이나 섭취 필요도를 예측한 결과가 아니에요.</p>
    {cards.length > 0 && !allowProductBrowsing && <button onClick={onOpenExistingSafetyFlow}>제품 정보 확인 절차로 이동</button>}
    {allowProductBrowsing && <>
      <nav aria-label="선택한 관심 항목">{cards.map(card => <button key={card.id}
        aria-pressed={active === card.id} onClick={() => { setActive(card.id); resetFilters(); }}>{card.label}</button>)}</nav>
      {result && <>
        <h3>{cards.find(x => x.id === active)?.title}</h3>
        <p>{result.sourceLabel} · {result.sortLabel} · {result.total.toLocaleString()}개</p>
        <label>제품 검색 <input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} /></label>
        <label>제형 <select value={form} onChange={e => { setForm(e.target.value); setPage(1); }}><option value="">전체</option>{result.facets.forms.map(x => <option key={x}>{x}</option>)}</select></label>
        <label>제품 구성 <select value={pool} onChange={e => { setPool(e.target.value); setPage(1); }}><option value="">전체</option>{result.facets.pools.map(x => <option key={x}>{x}</option>)}</select></label>
        <label>하루 섭취 개수 <select value={maxDailyUnits ?? ''} onChange={e => { setMaxDailyUnits(e.target.value ? Number(e.target.value) : null); setPage(1); }}><option value="">전체</option><option value="1">1개 이하</option><option value="2">2개 이하</option></select></label>
        <label>페이지당 <select value={pageSize} onChange={e => { setPageSize(Number(e.target.value)); setPage(1); }}>{[12,16,20].map(x => <option key={x} value={x}>{x}개</option>)}</select></label>
        {active === 'eye' && <label><input type="checkbox" checked={eyeOmega} onChange={e => { setEyeOmega(e.target.checked); setPage(1); }} />건조한 눈 개선 기능이 표시된 오메가3도 함께 보기</label>}
        {result.total === 0 && <p>선택한 조건에 맞는 제품이 없어요. 필터를 바꿔 보세요.</p>}
        <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(240px, 1fr))', gap:16}}>
          {result.items.map(p => <article key={p.id} style={{border:'1px solid #ddd', padding:16}}>
            <h4>{p.name}</h4><p>{p.manufacturer} · {p.form} · {p.pool}</p>
            <p>{p.dailyIntakeText}</p>
            <details><summary>기능성·주의사항 확인</summary>
              <p style={{whiteSpace:'pre-wrap'}}>{p.functionText}</p>
              <p style={{whiteSpace:'pre-wrap'}}>{p.cautionText}</p>
              <p>함께 든 성분: {p.companionIngredients || '표시 정보 없음'}</p>
              <p>품목제조신고번호: {p.id}</p>
            </details>
          </article>)}
        </div>
        {result.totalPages > 0 && <div><button disabled={result.page <= 1} onClick={() => setPage(result.page - 1)}>이전</button>
          <span aria-live="polite"> {result.page} / {result.totalPages} </span>
          <button disabled={result.page >= result.totalPages} onClick={() => setPage(result.page + 1)}>다음</button></div>}
      </>}
    </>}
  </section>;
}
