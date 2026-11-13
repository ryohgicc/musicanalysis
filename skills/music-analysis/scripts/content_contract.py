"""Content requirements for the approved report layout, distinct from data validity."""


def validate_complete(report):
    errors = []

    def text(value, label, maximum):
        if not isinstance(value, str) or not value.strip():
            errors.append(f'{label}: required')
        elif len(value) > maximum:
            errors.append(f'{label}: {len(value)} characters exceeds {maximum}')

    text(report.get('title'), 'title', 18)
    text(report.get('summary'), 'summary', 60)
    stages = report.get('stages', [])
    insights = report.get('insights', [])
    recs = report.get('recommendations', [])
    for label, items, count in [('stages', stages, 9), ('insights', insights, 6), ('recommendations', recs, 12)]:
        if len(items) != count:
            errors.append(f'{label}: complete layout requires {count}, received {len(items)}')
    for i, stage in enumerate(stages, 1):
        for field, maximum in [('tag', 6), ('title', 22), ('subtitle', 45), ('body', 190), ('insight', 50)]:
            text(stage.get(field), f'stage {i}.{field}', maximum)
        if len(stage.get('anchorIds', [])) != 3 or len(set(stage.get('anchorIds', []))) != 3:
            errors.append(f'stage {i}: needs 3 distinct evidence tracks')
    for i, insight in enumerate(insights, 1):
        for field, maximum in [('kicker', 28), ('title', 24), ('summary', 65), ('body', 190), ('direction', 100), ('question', 80)]:
            text(insight.get(field), f'insight {i}.{field}', maximum)
        if len(insight.get('evidence', [])) != 3 or len({e['index'] for e in insight.get('evidence', [])}) != 3:
            errors.append(f'insight {i}: needs 3 distinct evidence tracks')
        for j, evidence in enumerate(insight.get('evidence', []), 1):
            text(evidence.get('note'), f'insight {i}.evidence {j}.note', 70)
        if not 1 <= len(insight.get('recommendationIds', [])) <= 3:
            errors.append(f'insight {i}: needs 1–3 explicit recommendationIds')
    for tier, count in [('大概率合口味', 6), ('相邻风格', 4), ('探索', 2)]:
        if sum(r.get('tier') == tier for r in recs) != count:
            errors.append(f'recommendations: requires {count} in {tier}')
    for i, rec in enumerate(recs, 1):
        text(rec.get('reason'), f'recommendation {i}.reason', 100)
        text(rec.get('difference'), f'recommendation {i}.difference', 70)
    if errors:
        raise ValueError('Incomplete report content:\n- ' + '\n- '.join(errors) +
                         '\nComplete the analysis or use --preview; do not present a preview as a finished report.')
