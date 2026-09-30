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
                if (!isNaN(data[key]) && data[key] !== '' && form.querySelector(`[name="${key}"]`).type === 'number') {
                    data[key] = Number(data[key]);
                }
            }

            const toolId = form.id.replace('form-', '');
            const endpoint = `/api/${toolId.replace('-', '_')}`;

            // Show loader
            resultOutput.style.display = 'none';
            loader.style.display = 'block';

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
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
});
