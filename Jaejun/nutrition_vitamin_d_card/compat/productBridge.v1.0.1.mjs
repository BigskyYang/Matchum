// Pure ES module: no model changes, network calls, or new product scoring.
const MODEL_TO_CATEGORY = Object.freeze({
  magnesium: 'magnesium', vitamin_b1: 'vitamin_b', vitamin_b2: 'vitamin_b',
  vitamin_c: 'vitamin_c', fiber: 'fiber', zinc: 'zinc', folate: 'folate',
  iron: 'iron', calcium: 'calcium',
});
const FOOD_ONLY = new Set(['protein', 'phosphorus', 'potassium', 'vitamin_a', 'sodium_excess']);
const INFORMATION_ONLY = new Set(['vitamin_d', 'multi_balance', 'multi_energy']);

function strings(value, name) {
  if (!Array.isArray(value) || value.some(x => typeof x !== 'string'))
    throw new TypeError(`${name} must be a string array`);
  return [...new Set(value)];
}

/** Input selectedNutrientIds comes from the existing web selection, not raw probabilities. */
export function buildProductResult(catalog, options = {}) {
  const selected = strings(options.selectedNutrientIds ?? [], 'selectedNutrientIds');
  const information = strings(options.informationCategoryIds ?? [], 'informationCategoryIds');
  const target = options.target ?? '일반';
  if (!catalog.targets.includes(target)) throw new RangeError('Unknown source target');
  const pageSize = options.pageSize ?? 20;
  if (!Number.isInteger(pageSize) || pageSize < 12 || pageSize > 20)
    throw new RangeError('pageSize must be an integer from 12 to 20');
  const requests = new Map();
  const foodOnlyNutrients = [];
  for (const id of selected) {
    if (FOOD_ONLY.has(id)) { foodOnlyNutrients.push(id); continue; }
    const category = MODEL_TO_CATEGORY[id];
    if (!category) throw new RangeError(`Unknown model nutrient: ${id}`);
    if (!requests.has(category)) requests.set(category, { kind: 'model_nutrient', ids: [] });
    requests.get(category).ids.push(id);
  }
  for (const category of information) {
    if (!INFORMATION_ONLY.has(category)) throw new RangeError(`Not an information category: ${category}`);
    requests.set(category, { kind: 'information_only', ids: [] });
  }
  const uniqueCandidates = new Set();
  const uniqueVisible = new Set();
  const groups = [];
  for (const category of [...catalog.categories].sort((a, b) => a.order - b.order)) {
    const request = requests.get(category.category_id);
    if (!request) continue;
    const forms = strings(options.filters?.[category.category_id]?.forms ?? [], 'forms');
    const all = catalog.links.filter(x => x.category_id === category.category_id && x.target === target)
      .sort((a, b) => a.source_order - b.source_order);
    const filtered = all.filter(x => !forms.length || forms.includes(catalog.products[x.product_id].form));
    for (const row of filtered) uniqueCandidates.add(row.product_id);
    const page = options.pages?.[category.category_id] ?? 1;
    if (!Number.isInteger(page) || page < 1) throw new RangeError('page must be a positive integer');
    const pageRows = filtered.slice((page - 1) * pageSize, page * pageSize);
    const items = pageRows.map(row => {
      uniqueVisible.add(row.product_id);
      const p = catalog.products[row.product_id];
      return {
        ...p, source_product_type: row.source_product_type,
        daily_amount: row.daily_amount, daily_unit: row.daily_unit,
        daily_reference_percent: row.daily_reference_percent,
        connection_kind: request.kind, linked_nutrient_ids: [...request.ids],
        connection_label: request.kind === 'information_only'
          ? `${category.label} 일반 정보 목록`
          : `${category.label} 관련 제품 목록`,
        // A source classification can include a main nutrient plus an auxiliary.
        // No additional composition claim or dosage is inferred here.
        feature_labels: [p.intake_label, p.form].filter(Boolean),
      };
    });
    groups.push({
      category_id: category.category_id, label: category.label, target,
      connection_kind: request.kind, linked_nutrient_ids: [...request.ids],
      unfiltered_count: all.length, total_count: filtered.length,
      available_forms: [...new Set(all.map(x => catalog.products[x.product_id].form))].sort(),
      page, page_size: pageSize, page_count: Math.ceil(filtered.length / pageSize),
      has_previous: filtered.length > 0 && page > 1,
      has_next: page * pageSize < filtered.length, items,
    });
  }
  return {
    bridge_version: '1.0.1', catalog_version: catalog.catalog_version,
    selection_status: requests.size ? 'provided_by_web' : 'no_categories_requested',
    target, groups, food_only_nutrient_ids: foodOnlyNutrients,
    unique_candidate_product_count: uniqueCandidates.size,
    unique_visible_product_count: uniqueVisible.size,
    display_policy: { show_scores: false, show_product_grades: false,
      order: 'source_category_order_then_source_order_within_target',
      product_limit: null, default_page_size: 20 },
  };
}

/** Existing model example uses display_summary.selected_nutrients (objects with nutrient_id). */
export function fromModelResponse(catalog, modelResponse, options = {}) {
  let ids = options.selectedNutrientIds;
  if (ids === undefined) {
    const selection = modelResponse?.display_summary?.selected_nutrients ?? [];
    if (!Array.isArray(selection)) throw new TypeError('selected_nutrients must be an array');
    ids = selection.map(x => typeof x === 'string' ? x : x?.nutrient_id);
  }
  // An empty selection stays empty; we never infer categories from risk_band or probability.
  return buildProductResult(catalog, { ...options, selectedNutrientIds: ids });
}

/** Options for the PERSONAL result dropdown; general information stays separate. */
export function getNutrientDropdownOptions(result) {
  if (!Array.isArray(result?.groups)) throw new TypeError('result.groups must be an array');
  return result.groups.filter(g => g.connection_kind === 'model_nutrient').map(g => ({
    value: g.category_id,
    label: g.label,
    count: g.unfiltered_count,
    disabled: g.unfiltered_count === 0,
    linked_nutrient_ids: [...g.linked_nutrient_ids],
  }));
}
