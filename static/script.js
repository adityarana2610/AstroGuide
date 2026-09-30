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
                if (field && !isNaN(data[key]) && data[key] !== '' && field.type === 'number') {
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
        
        // Custom rendering for birth chart to show SVG
        if (toolId === 'birth-chart' && data.svg_chart) {
            html += `<h4>Birth Chart</h4>`;
            html += `<div class="svg-container">${data.svg_chart}</div>`;
            // Remove svg_chart from data before stringifying the rest
            const { svg_chart, ...rest } = data;
            html += `<h4 style="margin-top:20px;">Raw Data</h4><pre>${JSON.stringify(rest, null, 2)}</pre>`;
        } else {
            // Generic rendering
            html += `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        }
        
        html += '</div>';
        resultOutput.innerHTML = html;
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
            const preview = JSON.stringify(chart.data, null, 2).slice(0, 700);
            return `<article class="history-item"><strong>${escapeHtml(chart.tool)}</strong><time>${escapeHtml(chart.created_at)}</time><pre>${escapeHtml(preview)}</pre></article>`;
        }).join('') + '</div>';
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
