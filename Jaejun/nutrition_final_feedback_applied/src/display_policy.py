"""Probability-free UI projection; nutrient selection remains owned by the web."""
LABELS={'High':'높은 편','Mid':'보통','Low':'낮은 편'}
DISCLAIMER='기준 자료 안에서의 상대 등급이며, 부족을 진단한 결과가 아니고 필요한 양을 알려주지 않습니다.'

def build_display_summary(lifestyle,habitual,selected_ids=None):
    # Web selection order is supplied explicitly; never rank different nutrients
    # by uncalibrated cross-nutrient probability values.
    rows={}
    for nutrient,ls in lifestyle.items():
        ffq=habitual.get(nutrient) if habitual else None
        chosen=ffq if ffq is not None else ls
        source='habitual_diet' if ffq is not None else 'lifestyle'
        rows[nutrient]={
            'nutrient_id':nutrient,'risk_band':chosen['risk_band'],
            'display_label':LABELS[chosen['risk_band']],
            'display_source':source,
            'signals_differ':ffq is not None and ls['risk_band']!=ffq['risk_band'],
            'lifestyle_label':LABELS[ls['risk_band']],
            'habitual_diet_label':LABELS[ffq['risk_band']] if ffq else None,
        }
    selected=[]
    if selected_ids is not None:
        if not isinstance(selected_ids,list) or len(selected_ids)>5:
            raise ValueError('Web selection must be a list of at most five nutrient IDs')
        if any(not isinstance(n,str) for n in selected_ids):raise ValueError('Nutrient IDs must be strings')
        if len(set(selected_ids))!=len(selected_ids):raise ValueError('Duplicate nutrient IDs in selection')
        if any(n not in rows for n in selected_ids):raise ValueError('Unknown nutrient ID in selection')
        selected=[rows[n] for n in selected_ids]
    return {
        'show_probability_numbers':False,'max_selected_nutrients':5,
        'disagreement_policy':'prefer_habitual_diet_when_available',
        'selection_status':'managed_by_web' if selected_ids is None else 'validated_web_selection',
        'nutrients':rows,'selected_nutrients':selected,'disclaimer':DISCLAIMER,
    }
