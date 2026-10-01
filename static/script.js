document.addEventListener('DOMContentLoaded', () => {
    // Navigation
    const navBtns = document.querySelectorAll('.nav-btn');
    const sections = document.querySelectorAll('.tool-section');
    const resultOutput = document.getElementById('result-output');
    const loader = document.getElementById('loader');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active states
            navBtns.forEach(b => b.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(btn.dataset.target).classList.add('active');

            if (btn.dataset.target === 'profile') {
                loadProfile();
            }
            
            // Clear results
            resultOutput.innerHTML = '<div class="placeholder-text">Fill out a form and submit to see results.</div>';
        });
    });

    // Form Handling
    const forms = document.querySelectorAll('.tool-form');
    
    forms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            
            // Convert numerical types
            for (let key in data) {
                const field = form.querySelector(`[name="${key}"]`);
                if (field && !isNaN(data[key]) && data[key] !== '' && (field.type === 'number' || field.dataset.type === 'number')) {
                    data[key] = Number(data[key]);
                }
            }

            const toolId = form.id.replace('form-', '');
            const endpoint = toolId === 'rag' ? '/api/rag' : `/api/${toolId.replace('-', '_')}`;
            const method = toolId === 'profile' ? 'PUT' : 'POST';

            // Show loader
            resultOutput.style.display = 'none';
            loader.style.display = 'block';

            try {
                const response = await fetch(endpoint, {
                    method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                loader.style.display = 'none';
                resultOutput.style.display = 'block';

                let errorMsg = null;
                if (!result.success) {
                    if (result.error) {
                        errorMsg = result.error;
                    } else if (result.detail) {
                        if (Array.isArray(result.detail)) {
                            errorMsg = result.detail.map(d => `${d.loc ? d.loc[d.loc.length - 1] + ': ' : ''}${d.msg}`).join(', ');
                        } else {
                            errorMsg = String(result.detail);
                        }
                    } else {
                        errorMsg = 'An unknown error occurred';
                    }
                } else if (result.data && result.data.error) {
                    errorMsg = result.data.error;
                }

                if (errorMsg) {
                    resultOutput.innerHTML = `<div class="result-data" style="color: #ef4444;">Error: ${errorMsg}</div>`;
                } else {
                    renderResult(toolId, result.data);
                    if (toolId !== 'profile' && toolId !== 'rag') {
                        await saveGeneratedResult(toolId, result.data);
                    }
                }
            } catch (err) {
                loader.style.display = 'none';
                resultOutput.style.display = 'block';
                resultOutput.innerHTML = `<div class="result-data" style="color: #ef4444;">Network Error: ${err.message}</div>`;
            }
        });
    });

    function renderResult(toolId, data) {
        let html = '<div class="result-data">';

        if (toolId === 'profile') {
            html += '<strong>Profile saved.</strong><p class="profile-save-note">Your saved details are now available to AstroGuide RAG.</p>';
            html += '</div>';
            resultOutput.innerHTML = html;
            updateProfileView(data);
            return;
        }

        if (toolId === 'rag') {
            html += `<div class="rag-answer">${formatAnswer(data.response)}</div>`;
            html += `<div class="rag-meta">${escapeHtml(data.action_name || 'Direct generation')}`;
            if (data.rewritten_query) {
                html += ` - rewritten query: ${escapeHtml(data.rewritten_query)}`;
            }
            html += '</div>';
            if (data.retrieved_docs && data.retrieved_docs.length) {
                html += '<details class="rag-sources"><summary>Retrieved sources</summary><ul>';
                data.retrieved_docs.forEach(doc => {
                    html += `<li>${escapeHtml(doc.section_title || doc.metadata?.doc_name || 'Indexed note')}: ${escapeHtml(doc.text)}</li>`;
                });
                html += '</ul></details>';
            }
            html += '</div>';
            resultOutput.innerHTML = html;
            return;
        }

        // Section-specific rich renderers
        html += '<div class="result-card">';

        if (toolId === 'birth-chart') {
            html += renderBirthChart(data);
        } else if (toolId === 'numbers-stones') {
            html += renderNumbersStones(data);
        } else if (toolId === 'daily-transits') {
            html += renderDailyTransits(data);
        } else if (toolId === 'compatibility') {
            html += renderCompatibility(data);
        } else if (toolId === 'find-dates') {
            html += renderFindDates(data);
        } else {
            html += `<div class="placeholder-text">Result received.</div>`;
        }

        html += `</div></div>`;
        resultOutput.innerHTML = html;
    }

    function renderDailyTransits(data) {
        const sum = data.summary || {};
        const score = sum.overall_score || 0;
        const scoreClass = score > 0 ? 'badge-fav' : (score < 0 ? 'badge-unfav' : 'badge-info');
        const scoreVerdict = score >= 3 ? 'Highly Favourable' : (score > 0 ? 'Favourable' : (score === 0 ? 'Neutral' : 'Challenging'));

        let h = `
            <div class="results-header">
                <div>
                    <h4>🌍 Daily Transits</h4>
                    <div class="results-subtitle">Natal Moon: <strong>${escapeHtml(data.natal_moon_sign)}</strong> | Date: <strong>${escapeHtml(data.date)}</strong></div>
                </div>
                <span class="badge ${scoreClass}" style="font-size:0.95rem; padding: 6px 16px;">
                    ${score > 0 ? '+' : ''}${score} (${scoreVerdict})
                </span>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-val" style="color: #34d399;">${sum.favourable_count ?? 0}</div>
                    <div class="stat-lbl">Favourable</div>
                </div>
                <div class="stat-card">
                    <div class="stat-val" style="color: #f87171;">${sum.unfavourable_count ?? 0}</div>
                    <div class="stat-lbl">Unfavourable</div>
                </div>
                <div class="stat-card">
                    <div class="stat-val" style="color: #fbbf24;">${sum.blocked_count ?? 0}</div>
                    <div class="stat-lbl">Vedha Blocked</div>
                </div>
                <div class="stat-card">
                    <div class="stat-val" style="color: #a78bfa;">${score > 0 ? '+' : ''}${score}</div>
                    <div class="stat-lbl">Overall Score</div>
                </div>
            </div>

            <h5 style="margin-top: 8px; font-weight:700;">Planetary Transits Breakdown</h5>
            <div class="astro-table-container">
                <table class="astro-table">
                    <thead>
                        <tr>
                            <th>Planet</th>
                            <th>Transit Sign</th>
                            <th>House From Moon</th>
                            <th>Influence</th>
                            <th>Vedha Obstruction</th>
                            <th>Score</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        (data.transits || []).forEach(t => {
            const infBadge = t.is_favourable 
                ? '<span class="badge badge-fav">Favourable</span>' 
                : '<span class="badge badge-unfav">Unfavourable</span>';
            
            const vedhaBadge = t.vedha_blocked 
                ? `<span class="badge badge-warn">Blocked by ${escapeHtml(t.vedha_blocked_by || 'Planet')}</span>`
                : '<span class="badge badge-info">Clear</span>';

            const scoreText = t.score > 0 ? `+${t.score}` : `${t.score}`;
            const scoreColor = t.score > 0 ? '#34d399' : (t.score < 0 ? '#f87171' : '#94a3b8');

            h += `
                <tr>
                    <td><strong>${escapeHtml(t.planet)}</strong></td>
                    <td>${escapeHtml(t.sign)}</td>
                    <td>House ${t.house_from_moon}</td>
                    <td>${infBadge}</td>
                    <td>${vedhaBadge}</td>
                    <td style="font-weight:700; color:${scoreColor};">${scoreText}</td>
                </tr>
            `;
        });

        h += `</tbody></table></div>`;
        return h;
    }

    function renderNumbersStones(data) {
        let h = `
            <div class="results-header">
                <div>
                    <h4>💎 Numerology & Astro Gemstones</h4>
                    <div class="results-subtitle">Birth Date: <strong>${escapeHtml(data.birth_date)}</strong></div>
                </div>
            </div>

            <div class="feature-grid">
                <div class="feature-card">
                    <div class="feature-num-box">${data.driver_number}</div>
                    <div class="feature-info">
                        <h5>Driver (Mulank / Psychic)</h5>
                        <div class="feature-title">${escapeHtml(data.driver_planet)}</div>
                        <div class="feature-sub">Ruling Planet</div>
                    </div>
                </div>
                <div class="feature-card">
                    <div class="feature-num-box">${data.conductor_number}</div>
                    <div class="feature-info">
                        <h5>Conductor (Bhagyank / Destiny)</h5>
                        <div class="feature-title">${escapeHtml(data.conductor_planet)}</div>
                        <div class="feature-sub">Life Path Ruler</div>
                    </div>
                </div>
            </div>

            <h5 style="margin-top: 8px; font-weight:700;">Recommended Gemstones</h5>
            <div class="gem-grid">
                <div class="gem-card">
                    <div class="gem-icon">💎</div>
                    <div class="gem-meta">
                        <h6>Primary Gemstone</h6>
                        <div class="gem-name">${escapeHtml(data.primary_gemstone)}</div>
                    </div>
                </div>
                <div class="gem-card">
                    <div class="gem-icon">✨</div>
                    <div class="gem-meta">
                        <h6>Secondary Gemstone</h6>
                        <div class="gem-name">${escapeHtml(data.secondary_gemstone)}</div>
                    </div>
                </div>
            </div>

            <div class="feature-card" style="flex-direction: column; align-items: flex-start; gap: 14px;">
                <h5 style="color:var(--text-muted); text-transform:uppercase; font-size:0.78rem; letter-spacing:0.05em;">Lucky Numbers</h5>
                <div class="pills-container">
                    ${(data.lucky_numbers || []).map(n => `<span class="pill" style="font-size:1.05rem; font-weight:800; border-color: rgba(99, 102, 241, 0.4);">${n}</span>`).join('')}
                </div>

                <h5 style="color:var(--text-muted); text-transform:uppercase; font-size:0.78rem; letter-spacing:0.05em; margin-top:6px;">Lucky Colours</h5>
                <div class="pills-container">
                    ${(data.lucky_colours || []).map(c => `
                        <span class="pill">
                            <span class="pill-dot" style="background:${getColorHex(c)};"></span>
                            ${escapeHtml(c)}
                        </span>
                    `).join('')}
                </div>

                <h5 style="color:var(--text-muted); text-transform:uppercase; font-size:0.78rem; letter-spacing:0.05em; margin-top:6px;">Planetary Harmony</h5>
                <div class="pills-container">
                    ${(data.friendly_planets || []).map(p => `<span class="badge badge-fav">Friendly: ${escapeHtml(p)}</span>`).join('')}
                    ${(data.unfriendly_planets || []).map(p => `<span class="badge badge-unfav">Enemy: ${escapeHtml(p)}</span>`).join('')}
                </div>
            </div>

            <h5 style="margin-top: 8px; font-weight:700;">Astrological Remedies</h5>
            <div class="remedy-grid">
                <div class="remedy-card">
                    <h5>✨ Remedies for ${escapeHtml(data.driver_planet)}</h5>
                    <ul>
                        ${formatRemediesList(data.driver_remedies, data.driver_remedy)}
                    </ul>
                </div>
                <div class="remedy-card alt">
                    <h5>🌟 Remedies for ${escapeHtml(data.conductor_planet)}</h5>
                    <ul>
                        ${formatRemediesList(data.conductor_remedies, data.conductor_remedy)}
                    </ul>
                </div>
            </div>
        `;
        return h;
    }

    function formatRemediesList(remediesObj, singleRemedyStr) {
        if (!remediesObj && !singleRemedyStr) return '<li>No specific remedies listed.</li>';
        if (typeof remediesObj === 'string') return `<li>${escapeHtml(remediesObj)}</li>`;
        if (Array.isArray(remediesObj)) return remediesObj.map(r => `<li>${escapeHtml(r)}</li>`).join('');
        if (typeof remediesObj === 'object') {
            const items = [];
            if (remediesObj.mantra) items.push(`<strong>Mantra:</strong> <em>${escapeHtml(remediesObj.mantra)}</em>`);
            if (remediesObj.deity) items.push(`<strong>Deity:</strong> ${escapeHtml(remediesObj.deity)}`);
            if (remediesObj.fasting_day) items.push(`<strong>Fasting:</strong> ${escapeHtml(remediesObj.fasting_day)}${remediesObj.fasting_rules ? ` — ${escapeHtml(remediesObj.fasting_rules)}` : ''}`);
            if (remediesObj.wear_finger) items.push(`<strong>Wear Gem:</strong> ${escapeHtml(remediesObj.wear_finger)} (${escapeHtml(remediesObj.wear_day || '')}, in ${escapeHtml(remediesObj.metal || '')})`);
            if (remediesObj.charity_items && remediesObj.charity_items.length) {
                items.push(`<strong>Charity / Donations:</strong> ${escapeHtml(remediesObj.charity_items.slice(0, 4).join(', '))}`);
            }
            if (remediesObj.positive_lifestyle_action) items.push(`<strong>Lifestyle:</strong> ${escapeHtml(remediesObj.positive_lifestyle_action)}`);
            if (items.length) return items.map(it => `<li>${it}</li>`).join('');
        }
        return singleRemedyStr ? `<li>${escapeHtml(singleRemedyStr)}</li>` : '<li>General planetary meditation and charitable donation.</li>';
    }

    function renderCompatibility(data) {
        const p1 = data.person1 || {};
        const p2 = data.person2 || {};
        const score = data.total_score ?? 0;
        const maxScore = data.max_score || 36;
        const pct = data.percentage ?? Math.round((score / maxScore) * 100);
        const verdictBadgeClass = pct >= 70 ? 'badge-fav' : (pct >= 50 ? 'badge-warn' : 'badge-unfav');

        let h = `
            <div class="results-header">
                <div>
                    <h4>❤️ Ashtakoota Guna Milan</h4>
                    <div class="results-subtitle">Partner 1: <strong>${escapeHtml(p1.nakshatra || '')} (Pada ${p1.pada || 1})</strong> vs Partner 2: <strong>${escapeHtml(p2.nakshatra || '')} (Pada ${p2.pada || 1})</strong></div>
                </div>
            </div>

            <div class="compat-banner">
                <div class="compat-score-num">${score} <span class="compat-score-total">/ ${maxScore}</span></div>
                <div class="progress-track">
                    <div class="progress-fill" style="width: ${pct}%;"></div>
                </div>
                <span class="badge ${verdictBadgeClass}" style="font-size: 1.05rem; padding: 8px 20px;">
                    ${escapeHtml(data.verdict || 'Match Complete')} (${pct}%)
                </span>
            </div>

            <div class="dosha-box">
                <div class="dosha-item ${data.doshas?.nadi_dosha ? 'alert' : 'clean'}">
                    <span>${data.doshas?.nadi_dosha ? '⚠️' : '✅'}</span>
                    <div>
                        <strong>Nadi Dosha:</strong> ${data.doshas?.nadi_dosha ? 'Present (Nadi mismatch detected)' : 'None (Healthy Nadi alignment)'}
                    </div>
                </div>
                <div class="dosha-item ${data.doshas?.bhakoot_dosha ? 'alert' : 'clean'}">
                    <span>${data.doshas?.bhakoot_dosha ? '⚠️' : '✅'}</span>
                    <div>
                        <strong>Bhakoot Dosha:</strong> ${data.doshas?.bhakoot_dosha ? 'Present (6/8 or 9/5 moon sign offset)' : 'None (Auspicious Bhakoot relationship)'}
                    </div>
                </div>
            </div>

            <h5 style="margin-top: 8px; font-weight:700;">8 Kootas Detailed Breakdown</h5>
            <div class="astro-table-container">
                <table class="astro-table">
                    <thead>
                        <tr>
                            <th>Koota (Guna)</th>
                            <th>Points</th>
                            <th>Max</th>
                            <th>Description / Significance</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        (data.kootas || []).forEach(k => {
            const pts = k.obtained ?? 0;
            const max = k.maximum ?? 0;
            const isFull = pts === max && max > 0;
            const badgeCls = isFull ? 'badge-fav' : (pts > 0 ? 'badge-info' : 'badge-unfav');

            h += `
                <tr>
                    <td><strong>${escapeHtml(k.name)}</strong></td>
                    <td><span class="badge ${badgeCls}">${pts}</span></td>
                    <td style="color:var(--text-muted); font-weight:600;">${max}</td>
                    <td style="color:var(--text-muted); font-size:0.86rem;">${escapeHtml(k.description || '')}</td>
                </tr>
            `;
        });

        h += `</tbody></table></div>`;
        return h;
    }

    function renderFindDates(data) {
        const count = data.auspicious_dates_count || (data.auspicious_dates ? data.auspicious_dates.length : 0);
        const scanned = data.total_days_scanned || 0;

        let h = `
            <div class="results-header">
                <div>
                    <h4>📅 Auspicious Dates (Muhurtha Search)</h4>
                    <div class="results-subtitle">Period: <strong>${escapeHtml(data.start_date)}</strong> to <strong>${escapeHtml(data.end_date)}</strong> (${scanned} days scanned)</div>
                </div>
                <span class="badge ${count > 0 ? 'badge-fav' : 'badge-warn'}" style="font-size:0.95rem; padding: 6px 16px;">
                    ${count} Auspicious Date${count === 1 ? '' : 's'} Found
                </span>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-val" style="color:#a78bfa;">${scanned}</div>
                    <div class="stat-lbl">Days Scanned</div>
                </div>
                <div class="stat-card">
                    <div class="stat-val" style="color:#34d399;">${count}</div>
                    <div class="stat-lbl">Auspicious Dates</div>
                </div>
            </div>
        `;

        if (!count || !data.auspicious_dates || data.auspicious_dates.length === 0) {
            h += `
                <div class="placeholder-text" style="padding: 30px; background: rgba(0,0,0,0.2); border-radius:14px; border:1px solid var(--glass-border);">
                    No dates met the strict auspicious criteria in this timeframe. Try expanding your search range.
                </div>
            `;
            return h;
        }

        h += `<h5 style="margin-top: 8px; font-weight:700;">Auspicious Windows</h5><div class="dates-list">`;

        data.auspicious_dates.forEach(d => {
            const siddhiBadges = [];
            if (d.is_amrit_siddhi) siddhiBadges.push('<span class="badge badge-siddhi">🌟 Amrit Siddhi</span>');
            if (d.is_sarvartha_siddhi) siddhiBadges.push('<span class="badge badge-siddhi">✨ Sarvartha Siddhi</span>');

            h += `
                <div class="date-card">
                    <div class="date-main">
                        <div class="date-val">📅 ${escapeHtml(d.date)}</div>
                        <div class="date-details">
                            <span>Tithi: <strong>${escapeHtml(d.tithi || '')}</strong></span>
                            <span>Nakshatra: <strong>${escapeHtml(d.nakshatra || '')}</strong></span>
                            <span>Yoga: <strong>${escapeHtml(d.yoga || '')}</strong></span>
                            <span>Chandrabala: <strong>House ${d.chandrabala_house || ''}</strong></span>
                            <span>Tarabala: <strong>${escapeHtml(d.tarabala_tara || '')}</strong></span>
                        </div>
                    </div>
                    <div class="date-badges">
                        <span class="badge badge-fav">Score: ${d.score}/5</span>
                        ${siddhiBadges.join('')}
                    </div>
                </div>
            `;
        });

        h += `</div>`;
        return h;
    }

    function renderBirthChart(data) {
        const asc = data.ascendant || {};
        let h = `
            <div class="results-header">
                <div>
                    <h4>🌌 Vedic Birth Chart (Kundali)</h4>
                    <div class="results-subtitle">
                        Born: <strong>${escapeHtml(data.birth_date)} ${escapeHtml(data.birth_time)}</strong> | 
                        Lat: ${data.latitude}°, Lon: ${data.longitude}° | 
                        Ayanamsha: <strong>${escapeHtml(data.ayanamsha || 'Lahiri')}</strong>
                    </div>
                </div>
            </div>

            <div class="feature-card">
                <div class="feature-num-box" style="font-size:1.4rem;">ASC</div>
                <div class="feature-info">
                    <h5>Lagna (Ascendant)</h5>
                    <div class="feature-title">${escapeHtml(asc.sign || 'Unknown')} (${asc.degree || 0}°)</div>
                    <div class="feature-sub">Nakshatra: <strong>${escapeHtml(asc.nakshatra || '')}</strong> (Pada ${asc.pada || 1})</div>
                </div>
            </div>
        `;

        if (data.svg_chart) {
            h += `
                <div class="svg-container">
                    ${data.svg_chart}
                </div>
            `;
        }

        if (data.planets && data.planets.length) {
            h += `
                <h5 style="margin-top: 14px; font-weight:700;">Planetary Coordinates & Houses</h5>
                <div class="astro-table-container">
                    <table class="astro-table">
                        <thead>
                            <tr>
                                <th>Planet</th>
                                <th>Sign</th>
                                <th>Degree</th>
                                <th>House</th>
                                <th>Nakshatra</th>
                                <th>Pada</th>
                                <th>Motion</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            data.planets.forEach(p => {
                const retroBadge = p.is_retrograde 
                    ? '<span class="badge badge-retro">Retrograde (R)</span>'
                    : '<span class="badge badge-info">Direct</span>';

                h += `
                    <tr>
                        <td><strong>${escapeHtml(p.name)}</strong></td>
                        <td>${escapeHtml(p.sign)}</td>
                        <td>${p.degree_in_sign ?? p.longitude}°</td>
                        <td>House ${p.house}</td>
                        <td>${escapeHtml(p.nakshatra || '')}</td>
                        <td>${p.pada || ''}</td>
                        <td>${retroBadge}</td>
                    </tr>
                `;
            });

            h += `</tbody></table></div>`;
        }

        return h;
    }

    function getColorHex(colorName) {
        const c = String(colorName || '').toLowerCase().trim();
        if (c.includes('red') || c.includes('ruby')) return '#ef4444';
        if (c.includes('saffron') || c.includes('orange')) return '#f97316';
        if (c.includes('yellow') || c.includes('gold')) return '#eab308';
        if (c.includes('green')) return '#10b981';
        if (c.includes('white') || c.includes('silver') || c.includes('pearl')) return '#f8fafc';
        if (c.includes('dark blue') || c.includes('navy')) return '#1e3a8a';
        if (c.includes('blue')) return '#3b82f6';
        if (c.includes('black')) return '#0f172a';
        if (c.includes('brown')) return '#78350f';
        if (c.includes('grey') || c.includes('gray')) return '#64748b';
        if (c.includes('purple') || c.includes('violet')) return '#8b5cf6';
        if (c.includes('pink')) return '#ec4899';
        return '#6366f1';
    }

    async function loadProfile() {
        try {
            const response = await fetch('/api/profile');
            const result = await response.json();
            if (result.success) {
                updateProfileView(result.data);
            }
        } catch (err) {
            console.warn('Could not load profile:', err);
        }
    }

    function updateProfileView(profile) {
        const form = document.getElementById('form-profile');
        if (!form || !profile) return;
        Object.entries(profile).forEach(([key, value]) => {
            const field = form.querySelector(`[name="${key}"]`);
            if (field && typeof value === 'string') field.value = value;
        });

        const history = document.getElementById('chart-history');
        const charts = profile.charts || [];
        if (!charts.length) {
            history.innerHTML = '<h4>Saved charts and tool results</h4><div class="placeholder-text">Generated results will appear here automatically.</div>';
            return;
        }
        history.innerHTML = '<h4>Saved charts and tool results</h4><div class="history-list">' + charts.slice().reverse().map(chart => {
            const toolName = formatToolName(chart.tool);
            const summaryHtml = formatHistorySummary(chart.tool, chart.data);
            return `
                <article class="history-item">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                        <span class="badge badge-info">${escapeHtml(toolName)}</span>
                        <time style="margin-top:0;">${escapeHtml(chart.created_at || '')}</time>
                    </div>
                    <div style="margin-top:8px; font-size:0.9rem; color:var(--text-main);">${summaryHtml}</div>
                </article>
            `;
        }).join('') + '</div>';
    }

    function formatToolName(tool) {
        const names = {
            'birth-chart': '🌌 Birth Chart',
            'numbers-stones': '💎 Numbers & Stones',
            'daily-transits': '🌍 Daily Transits',
            'compatibility': '❤️ Compatibility',
            'find-dates': '📅 Find Dates'
        };
        return names[tool] || tool;
    }

    function formatHistorySummary(tool, data) {
        if (!data) return '';
        if (tool === 'daily-transits') {
            const score = data.summary?.overall_score ?? 0;
            return `Moon Sign: <strong>${escapeHtml(data.natal_moon_sign || '')}</strong> | Date: <strong>${escapeHtml(data.date || '')}</strong> | Transit Score: <strong>${score > 0 ? '+' : ''}${score}</strong>`;
        }
        if (tool === 'numbers-stones') {
            return `Driver: <strong>${data.driver_number} (${escapeHtml(data.driver_planet || '')})</strong> | Conductor: <strong>${data.conductor_number} (${escapeHtml(data.conductor_planet || '')})</strong> | Gemstone: <strong>${escapeHtml(data.primary_gemstone || '')}</strong>`;
        }
        if (tool === 'compatibility') {
            return `Score: <strong>${data.total_score}/${data.max_score} (${data.percentage}%)</strong> — <em>${escapeHtml(data.verdict || '')}</em>`;
        }
        if (tool === 'find-dates') {
            return `Found <strong>${data.auspicious_dates_count || 0} Auspicious Dates</strong> (${escapeHtml(data.start_date || '')} to ${escapeHtml(data.end_date || '')})`;
        }
        if (tool === 'birth-chart') {
            return `Ascendant: <strong>${escapeHtml(data.ascendant?.sign || '')} (${data.ascendant?.degree || 0}°)</strong> | Born: <strong>${escapeHtml(data.birth_date || '')}</strong>`;
        }
        return '';
    }

    async function saveGeneratedResult(toolId, data) {
        try {
            const response = await fetch('/api/profile/charts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tool: toolId, data })
            });
            const result = await response.json();
            if (result.success) updateProfileView(result.data);
        } catch (err) {
            console.warn('Could not save generated result:', err);
        }
    }

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>'"]/g, character => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
        }[character]));
    }

    function formatAnswer(value) {
        return escapeHtml(value)
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
    }

    loadProfile();
});
