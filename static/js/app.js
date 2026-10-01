// AI Scholarship & Opportunity Matcher — Frontend Controller

(function () {
  const form = document.getElementById('profileForm');
  const skillsInput = document.getElementById('skillsInput');
  const skillsHidden = document.getElementById('skillsHidden');
  const skillsTags = document.getElementById('skillsTags');
  const interestsInput = document.getElementById('interestsInput');
  const interestsHidden = document.getElementById('interestsHidden');
  const interestsTags = document.getElementById('interestsTags');
  const loader = document.getElementById('loader');
  const loaderText = document.getElementById('loaderText');
  const toastContainer = document.getElementById('toastContainer');
  const btnMatch = document.getElementById('btnMatch');
  const btnReport = document.getElementById('btnReport');
  const btnClear = document.getElementById('btnClear');
  const btnDownload = document.getElementById('btnDownload');

  const state = {
    skills: [],
    interests: [],
    lastProfile: null,
    results: {},
    currentReportMarkdown: ''
  };

  // --- Tag Input Management ---

  function createTag(text, container, stateKey) {
    const tag = document.createElement('span');
    tag.className = 'tag';
    tag.innerHTML = `${escapeHtml(text)} <span class="remove">&times;</span>`;
    tag.querySelector('.remove').addEventListener('click', () => {
      state[stateKey] = state[stateKey].filter((t) => t !== text);
      renderTags(container, stateKey);
    });
    return tag;
  }

  function renderTags(container, stateKey) {
    container.innerHTML = '';
    state[stateKey].forEach((text) => {
      container.appendChild(createTag(text, container, stateKey));
    });
    updateHiddenInputs();
  }

  function updateHiddenInputs() {
    skillsHidden.value = JSON.stringify(state.skills);
    interestsHidden.value = JSON.stringify(state.interests);
  }

  function setupTagInput(input, container, stateKey) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const value = input.value.trim();
        if (value && !state[stateKey].includes(value)) {
          state[stateKey].push(value);
          renderTags(container, stateKey);
          input.value = '';
        }
      }
    });
  }

  setupTagInput(skillsInput, skillsTags, 'skills');
  setupTagInput(interestsInput, interestsTags, 'interests');

  // --- Navigation ---

  document.querySelectorAll('.nav-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const section = btn.dataset.section;
      showSection(section);
      updateNavActive(btn);
    });
  });

  function updateNavActive(activeBtn) {
    document.querySelectorAll('.nav-btn').forEach((btn) => {
      btn.classList.remove('bg-brand-50', 'text-brand-700', 'shadow-sm');
      btn.classList.add('text-slate-600', 'hover:bg-slate-50');
    });
    activeBtn.classList.remove('text-slate-600', 'hover:bg-slate-50');
    activeBtn.classList.add('bg-brand-50', 'text-brand-700', 'shadow-sm');
  }

  function showSection(sectionId) {
    document.querySelectorAll('.content-section').forEach((sec) => {
      sec.classList.add('hidden');
    });
    const target = document.getElementById(sectionId);
    if (target) {
      target.classList.remove('hidden');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  // --- Form Helpers ---

  function collectProfile() {
    const formData = new FormData(form);
    return {
      full_name: formData.get('full_name')?.trim() || '',
      education_level: formData.get('education_level')?.trim() || '',
      degree_branch: formData.get('degree_branch')?.trim() || '',
      year_of_study: formData.get('year_of_study')?.trim() || '',
      cgpa: formData.get('cgpa')?.trim() || '',
      college_name: formData.get('college_name')?.trim() || '',
      location: formData.get('location')?.trim() || '',
      skills: [...state.skills],
      interests: [...state.interests],
      career_goal: formData.get('career_goal')?.trim() || ''
    };
  }

  function validateProfile(profile) {
    const required = [
      'full_name', 'education_level', 'degree_branch', 'year_of_study',
      'cgpa', 'college_name', 'location', 'career_goal'
    ];
    for (const field of required) {
      if (!profile[field]) {
        return `${field.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())} is required.`;
      }
    }
    if (!profile.skills.length) return 'At least one skill is required.';
    if (!profile.interests.length) return 'At least one interest is required.';
    const cgpa = parseFloat(profile.cgpa);
    if (isNaN(cgpa) || cgpa < 0 || cgpa > 100) {
      return 'CGPA / Percentage must be a number between 0 and 100.';
    }
    return null;
  }

  // --- API Helpers ---

  async function postJSON(endpoint, body) {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.error || `Request failed with status ${response.status}`);
    }
    return data;
  }

  function setLoading(show, text = 'Analyzing profile with AI...') {
    loaderText.textContent = text;
    loader.classList.toggle('hidden', !show);
    loader.classList.toggle('flex', show);
  }

  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<p class="text-sm font-medium text-slate-800">${escapeHtml(message)}</p>`;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.classList.add('hiding');
      toast.addEventListener('animationend', () => toast.remove());
    }, 4000);
  }

  // --- Rendering ---

  function escapeHtml(text) {
    if (typeof text !== 'string') return String(text);
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function renderProgress(percentage) {
    const pct = Math.min(100, Math.max(0, Math.round(percentage || 0)));
    const radius = 26;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (pct / 100) * circumference;
    let colorClass = 'match-low';
    if (pct >= 80) colorClass = 'match-high';
    else if (pct >= 60) colorClass = 'match-medium';

    return `
      <div class="progress-ring">
        <svg width="64" height="64" viewBox="0 0 64 64">
          <defs>
            <linearGradient id="matchGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#1d4ed8;stop-opacity:1" />
            </linearGradient>
          </defs>
          <circle class="progress-ring-bg" cx="32" cy="32" r="${radius}"></circle>
          <circle class="progress-ring-bar" cx="32" cy="32" r="${radius}" stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"></circle>
        </svg>
        <div class="absolute inset-0 flex items-center justify-center text-xs font-bold text-slate-700">${pct}%</div>
      </div>
    `;
  }

  function renderScholarshipCard(item) {
    const pct = parseInt(item.match_percentage, 10) || 75;
    return `
      <div class="glass-card rounded-2xl p-5 hover:shadow-lg transition-shadow">
        <div class="flex justify-between items-start mb-3">
          <div>
            <span class="match-badge ${pct >= 80 ? 'match-high' : pct >= 60 ? 'match-medium' : 'match-low'}">${escapeHtml(item.category || 'General')}</span>
            <h4 class="font-bold text-slate-900 mt-2 text-lg">${escapeHtml(item.name)}</h4>
          </div>
          ${renderProgress(pct)}
        </div>
        <p class="text-sm text-slate-600 mb-3">${escapeHtml(item.description || '')}</p>
        <ul class="space-y-2 text-sm">
          <li><span class="font-semibold text-slate-700">Eligibility:</span> ${escapeHtml(item.eligibility || 'N/A')}</li>
          <li><span class="font-semibold text-slate-700">Benefits:</span> ${escapeHtml(item.benefits || 'N/A')}</li>
          <li><span class="font-semibold text-slate-700">Deadline:</span> ${escapeHtml(item.deadline || 'Rolling')}</li>
          <li><span class="font-semibold text-slate-700">Tips:</span> ${escapeHtml(item.tips || 'N/A')}</li>
        </ul>
        ${renderApplyLink(item.url)}
        ${renderResources(item.resources)}
      </div>
    `;
  }

  function renderInternshipCard(item) {
    return `
      <div class="glass-card rounded-2xl p-5 hover:shadow-lg transition-shadow">
        <h4 class="font-bold text-slate-900 text-lg mb-1">${escapeHtml(item.role)}</h4>
        <p class="text-sm text-brand-600 font-medium mb-3">${escapeHtml(item.company || '')}</p>
        <ul class="space-y-2 text-sm">
          <li><span class="font-semibold text-slate-700">Skills:</span> ${(item.required_skills || []).map(escapeHtml).join(', ') || 'N/A'}</li>
          <li><span class="font-semibold text-slate-700">Duration:</span> ${escapeHtml(item.duration || 'N/A')}</li>
          <li><span class="font-semibold text-slate-700">Eligibility:</span> ${escapeHtml(item.eligibility || 'N/A')}</li>
          <li><span class="font-semibold text-slate-700">Outcomes:</span> ${escapeHtml(item.learning_outcomes || 'N/A')}</li>
          <li><span class="font-semibold text-slate-700">Tips:</span> ${escapeHtml(item.tips || 'N/A')}</li>
        </ul>
        ${renderApplyLink(item.url)}
        ${renderResources(item.resources)}
      </div>
    `;
  }

  function renderHackathonCard(item) {
    return `
      <div class="glass-card rounded-2xl p-5 hover:shadow-lg transition-shadow">
        <span class="match-badge bg-blue-50 text-brand-700">${escapeHtml(item.type || 'Competition')}</span>
        <h4 class="font-bold text-slate-900 text-lg mt-2 mb-1">${escapeHtml(item.name)}</h4>
        <p class="text-sm text-slate-600 mb-3"><strong>Theme:</strong> ${escapeHtml(item.theme || 'Open')}</p>
        <ul class="space-y-2 text-sm">
          <li><span class="font-semibold text-slate-700">Eligibility:</span> ${escapeHtml(item.eligibility || 'N/A')}</li>
          <li><span class="font-semibold text-slate-700">Skills:</span> ${(item.required_skills || []).map(escapeHtml).join(', ') || 'N/A'}</li>
          <li><span class="font-semibold text-slate-700">Roadmap:</span> ${escapeHtml(item.roadmap || 'N/A')}</li>
          <li><span class="font-semibold text-slate-700">Tips:</span> ${escapeHtml(item.tips || 'N/A')}</li>
        </ul>
        ${renderApplyLink(item.official_link || item.url)}
        ${renderResources(item.resources)}
      </div>
    `;
  }

  function renderFellowshipCard(item) {
    return `
      <div class="glass-card rounded-2xl p-5 hover:shadow-lg transition-shadow">
        <span class="match-badge bg-purple-50 text-purple-700">${escapeHtml(item.type || 'Fellowship')}</span>
        <h4 class="font-bold text-slate-900 text-lg mt-2 mb-1">${escapeHtml(item.name)}</h4>
        <ul class="space-y-2 text-sm">
          <li><span class="font-semibold text-slate-700">Eligibility:</span> ${escapeHtml(item.eligibility || 'N/A')}</li>
          <li><span class="font-semibold text-slate-700">Benefits:</span> ${escapeHtml(item.benefits || 'N/A')}</li>
          <li><span class="font-semibold text-slate-700">Tips:</span> ${escapeHtml(item.tips || 'N/A')}</li>
        </ul>
        ${renderApplyLink(item.official_link || item.url)}
        ${renderResources(item.resources)}
      </div>
    `;
  }

  function renderApplyLink(url) {
    if (!url) return '';
    return `
      <div class="mt-4 pt-3 border-t border-slate-100">
        <a href="${escapeHtml(url)}" target="_blank" rel="noopener" class="btn-primary text-sm w-full justify-center">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
          Apply Now
        </a>
      </div>
    `;
  }

  function renderResources(resources) {
    if (!resources || !resources.length) return '';
    return `
      <div class="mt-4 pt-3 border-t border-slate-100">
        <p class="text-xs font-semibold text-slate-500 mb-1">Resources</p>
        <div class="flex flex-wrap gap-2">
          ${resources.map((r) => `<a href="${escapeHtml(r)}" target="_blank" rel="noopener" class="text-xs text-brand-600 hover:underline">${escapeHtml(r)}</a>`).join('')}
        </div>
      </div>
    `;
  }

  function renderCertification(item, index) {
    const icons = ['🌱', '📘', '🚀'];
    return `
      <div class="timeline-item">
        <div class="glass-card rounded-2xl p-5 ml-2">
          <div class="flex items-center gap-3 mb-2">
            <span class="text-2xl">${icons[index % icons.length]}</span>
            <span class="match-badge bg-brand-50 text-brand-700">${escapeHtml(item.level)}</span>
            <span class="text-xs text-slate-400">${escapeHtml(item.duration || '')}</span>
          </div>
          <h4 class="font-bold text-slate-900 text-lg">${escapeHtml(item.name)}</h4>
          <p class="text-sm text-slate-500 mb-2">${escapeHtml(item.provider || '')}</p>
          <p class="text-sm text-slate-700 mb-2"><strong>Learning Path:</strong> ${escapeHtml(item.learning_path || 'N/A')}</p>
          <p class="text-sm text-slate-700"><strong>Skills Gained:</strong> ${(item.skills_gained || []).map(escapeHtml).join(', ') || 'N/A'}</p>
          ${item.tips ? `<p class="text-sm text-slate-600 mt-2"><strong>Tips:</strong> ${escapeHtml(item.tips)}</p>` : ''}
          ${renderApplyLink(item.url)}
        </div>
      </div>
    `;
  }

  function renderSkillGap(data) {
    const analysis = data.analysis || data;
    const missing = analysis.missing_skills || [];
    const tech = analysis.recommended_technologies || [];
    const projects = analysis.suggested_projects || [];
    const tips = analysis.resume_tips || [];

    return `
      <div class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div class="bg-white/60 rounded-xl p-5">
            <h5 class="font-bold text-slate-900 mb-2">Current Skills</h5>
            <div class="flex flex-wrap gap-2">${(analysis.current_skills || []).map((s) => `<span class="tag">${escapeHtml(s)}</span>`).join('') || 'N/A'}</div>
          </div>
          <div class="bg-white/60 rounded-xl p-5">
            <h5 class="font-bold text-slate-900 mb-2">Missing Skills</h5>
            <div class="flex flex-wrap gap-2">${missing.map((s) => `<span class="tag bg-red-50 text-red-700 border-red-100">${escapeHtml(s)}</span>`).join('') || 'None identified'}</div>
          </div>
        </div>
        <div>
          <h5 class="font-bold text-slate-900 mb-2">Recommended Technologies</h5>
          <div class="flex flex-wrap gap-2">${tech.map((t) => `<span class="tag bg-green-50 text-green-700 border-green-100">${escapeHtml(t)}</span>`).join('')}</div>
        </div>
        <div>
          <h5 class="font-bold text-slate-900 mb-3">Suggested Projects</h5>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${projects.map((p) => `
              <div class="bg-white/60 rounded-xl p-4">
                <h6 class="font-semibold text-slate-900">${escapeHtml(p.title || p)}</h6>
                <p class="text-sm text-slate-600 mt-1">${escapeHtml(p.description || '')}</p>
                ${p.technologies ? `<p class="text-xs text-slate-500 mt-2">Tech: ${p.technologies.map(escapeHtml).join(', ')}</p>` : ''}
              </div>
            `).join('')}
          </div>
        </div>
        <div>
          <h5 class="font-bold text-slate-900 mb-2">Resume Improvement Tips</h5>
          <ul class="list-disc list-inside text-sm text-slate-700 space-y-1">
            ${Array.isArray(tips) ? tips.map((t) => `<li>${escapeHtml(t)}</li>`).join('') : `<li>${escapeHtml(tips)}</li>`}
          </ul>
        </div>
      </div>
    `;
  }

  function renderCareerReport(report) {
    const roadmap = report.career_roadmap || [];
    return `
      <div class="space-y-8">
        <div class="bg-brand-50 rounded-xl p-5 border border-brand-100">
          <h4 class="font-bold text-brand-900 mb-2">Executive Summary</h4>
          <p class="text-slate-700">${escapeHtml(report.summary || '')}</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div class="glass-card rounded-xl p-5">
            <h5 class="font-bold text-slate-900 mb-2">Top Scholarships</h5>
            <ul class="list-disc list-inside text-sm text-slate-700">${(report.top_scholarships || []).map((s) => `<li>${escapeHtml(s)}</li>`).join('') || 'N/A'}</ul>
          </div>
          <div class="glass-card rounded-xl p-5">
            <h5 class="font-bold text-slate-900 mb-2">Top Internships</h5>
            <ul class="list-disc list-inside text-sm text-slate-700">${(report.top_internships || []).map((s) => `<li>${escapeHtml(s)}</li>`).join('') || 'N/A'}</ul>
          </div>
          <div class="glass-card rounded-xl p-5">
            <h5 class="font-bold text-slate-900 mb-2">Top Competitions</h5>
            <ul class="list-disc list-inside text-sm text-slate-700">${(report.top_hackathons || []).map((s) => `<li>${escapeHtml(s)}</li>`).join('') || 'N/A'}</ul>
          </div>
          <div class="glass-card rounded-xl p-5">
            <h5 class="font-bold text-slate-900 mb-2">Recommended Certifications</h5>
            <ul class="list-disc list-inside text-sm text-slate-700">${(report.top_certifications || []).map((s) => `<li>${escapeHtml(s)}</li>`).join('') || 'N/A'}</ul>
          </div>
        </div>
        <div>
          <h4 class="font-bold text-slate-900 mb-4">Career Roadmap</h4>
          <div class="timeline">
            ${roadmap.map((stage) => `
              <div class="timeline-item">
                <div class="glass-card rounded-xl p-5 ml-2">
                  <div class="flex items-center justify-between mb-2">
                    <h5 class="font-bold text-slate-900">${escapeHtml(stage.stage)}</h5>
                    <span class="text-xs font-semibold text-brand-600 bg-brand-50 px-2 py-1 rounded-lg">${escapeHtml(stage.duration)}</span>
                  </div>
                  <ul class="list-disc list-inside text-sm text-slate-700">${(stage.actions || []).map((a) => `<li>${escapeHtml(a)}</li>`).join('')}</ul>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
        <div class="glass-card rounded-xl p-5">
          <h4 class="font-bold text-slate-900 mb-2">Application Strategy</h4>
          <p class="text-sm text-slate-700">${escapeHtml(report.application_strategy || '')}</p>
        </div>
        <div>
          <h4 class="font-bold text-slate-900 mb-2">Next Steps</h4>
          <ul class="list-disc list-inside text-sm text-slate-700">${(report.next_steps || []).map((s) => `<li>${escapeHtml(s)}</li>`).join('') || 'N/A'}</ul>
        </div>
      </div>
    `;
  }

  // --- Core Actions ---

  async function matchOpportunities() {
    const profile = collectProfile();
    const error = validateProfile(profile);
    if (error) {
      showToast(error, 'error');
      return;
    }
    state.lastProfile = profile;
    state.results = {};

    try {
      setLoading(true, 'Analyzing profile...');
      const profileData = await postJSON('/api/analyze-profile', profile);
      renderProfileSummary(profileData);
      state.results.profile = profileData;

      setLoading(true, 'Matching scholarships...');
      state.results.scholarships = await postJSON('/api/match-scholarships', profile);
      document.getElementById('scholarshipsGrid').innerHTML = (state.results.scholarships.matches || [])
        .map(renderScholarshipCard).join('') || '<p class="text-slate-500">No scholarships found.</p>';

      setLoading(true, 'Finding internships...');
      state.results.internships = await postJSON('/api/match-internships', profile);
      document.getElementById('internshipsGrid').innerHTML = (state.results.internships.matches || [])
        .map(renderInternshipCard).join('') || '<p class="text-slate-500">No internships found.</p>';

      setLoading(true, 'Searching hackathons...');
      state.results.hackathons = await postJSON('/api/match-hackathons', profile);
      document.getElementById('hackathonsGrid').innerHTML = (state.results.hackathons.matches || [])
        .map(renderHackathonCard).join('') || '<p class="text-slate-500">No competitions found.</p>';

      setLoading(true, 'Discovering fellowships...');
      state.results.fellowships = await postJSON('/api/match-fellowships', profile);
      document.getElementById('fellowshipsGrid').innerHTML = (state.results.fellowships.matches || [])
        .map(renderFellowshipCard).join('') || '<p class="text-slate-500">No fellowships found.</p>';

      setLoading(true, 'Generating certifications...');
      state.results.certifications = await postJSON('/api/generate-certifications', profile);
      const certItems = state.results.certifications.roadmap || state.results.certifications.matches || [];
      document.getElementById('certificationsTimeline').innerHTML = `
        <div class="timeline">${certItems.map((c, i) => renderCertification(c, i)).join('')}</div>
      ` || '<p class="text-slate-500">No certifications found.</p>';

      setLoading(true, 'Analyzing skill gaps...');
      state.results.skillGap = await postJSON('/api/skill-gap', profile);
      document.getElementById('skillGapContent').innerHTML = renderSkillGap(state.results.skillGap);

      setLoading(true, 'Building career report...');
      try {
        state.results.careerReport = await postJSON('/api/career-report', profile);
        const report = state.results.careerReport.report || state.results.careerReport;
        document.getElementById('reportContent').innerHTML = renderCareerReport(report);
        state.currentReportMarkdown = buildReportMarkdown(report);
      } catch (err) {
        document.getElementById('reportContent').innerHTML = `<p class="text-slate-500">Career report could not be generated. Use Generate Career Report to try again.</p>`;
      }

      showToast('Opportunities matched successfully!', 'success');
      btnDownload.classList.remove('hidden');
      showSection('scholarships');
      updateNavActive(document.querySelector('[data-section="scholarships"]'));
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  }

  function renderProfileSummary(data) {
    const summary = document.getElementById('profileSummary');
    const text = document.getElementById('summaryText');
    const tags = document.getElementById('summaryTags');
    summary.classList.remove('hidden');
    text.textContent = data.summary || 'Profile summary not available.';
    tags.innerHTML = '';
    (data.strengths || []).forEach((s) => {
      tags.innerHTML += `<span class="tag bg-green-50 text-green-700 border-green-100">${escapeHtml(s)}</span>`;
    });
    (data.suggested_focus_areas || []).forEach((s) => {
      tags.innerHTML += `<span class="tag bg-amber-50 text-amber-700 border-amber-100">${escapeHtml(s)}</span>`;
    });
  }

  async function generateCareerReport() {
    const profile = collectProfile();
    const error = validateProfile(profile);
    if (error) {
      showToast(error, 'error');
      return;
    }
    state.lastProfile = profile;

    try {
      setLoading(true, 'Building comprehensive career report...');
      state.results.careerReport = await postJSON('/api/career-report', profile);
      const report = state.results.careerReport.report || state.results.careerReport;
      document.getElementById('reportContent').innerHTML = renderCareerReport(report);
      state.currentReportMarkdown = buildReportMarkdown(report);
      showSection('report');
      updateNavActive(document.querySelector('[data-section="report"]'));
      btnDownload.classList.remove('hidden');
      showToast('Career report generated!', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  }

  function buildReportMarkdown(report) {
    const p = state.lastProfile || {};
    let md = `# AI Career Opportunity Report\n\n`;
    md += `**Generated by:** {{ company_name }} — {{ app_name }}\n`;
    md += `**Student:** ${p.full_name || ''}\n`;
    md += `**Program:** ${p.degree_branch || ''}, ${p.education_level || ''} — ${p.year_of_study || ''}\n`;
    md += `**Career Goal:** ${p.career_goal || ''}\n\n`;
    md += `## Summary\n${report.summary || ''}\n\n`;
    md += `## Top Scholarships\n${(report.top_scholarships || []).map((s) => `- ${s}`).join('\n')}\n\n`;
    md += `## Top Internships\n${(report.top_internships || []).map((s) => `- ${s}`).join('\n')}\n\n`;
    md += `## Top Competitions\n${(report.top_hackathons || []).map((s) => `- ${s}`).join('\n')}\n\n`;
    md += `## Recommended Certifications\n${(report.top_certifications || []).map((s) => `- ${s}`).join('\n')}\n\n`;
    md += `## Career Roadmap\n`;
    (report.career_roadmap || []).forEach((stage) => {
      md += `### ${stage.stage} (${stage.duration})\n${(stage.actions || []).map((a) => `- ${a}`).join('\n')}\n\n`;
    });
    md += `## Application Strategy\n${report.application_strategy || ''}\n\n`;
    md += `## Next Steps\n${(report.next_steps || []).map((s) => `- ${s}`).join('\n')}\n\n`;
    md += `---\nFor support, contact {{ support_email }}\n`;
    return md;
  }

  function downloadReport() {
    if (!state.currentReportMarkdown && state.results.careerReport) {
      state.currentReportMarkdown = buildReportMarkdown(state.results.careerReport.report || state.results.careerReport);
    }
    const markdown = state.currentReportMarkdown || generateFallbackMarkdown();
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `career-report-${(state.lastProfile?.full_name || 'student').replace(/\s+/g, '_')}.md`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast('Report downloaded!', 'success');
  }

  function generateFallbackMarkdown() {
    return `# AI Scholarship & Opportunity Matcher Report\n\nNo report data available. Please generate a career report first.\n`;
  }

  function clearForm() {
    form.reset();
    state.skills = [];
    state.interests = [];
    renderTags(skillsTags, 'skills');
    renderTags(interestsTags, 'interests');
    state.lastProfile = null;
    state.results = {};
    state.currentReportMarkdown = '';
    document.querySelectorAll('.content-section').forEach((sec) => {
      if (sec.id !== 'profile') sec.classList.add('hidden');
    });
    document.getElementById('profileSummary').classList.add('hidden');
    ['scholarshipsGrid', 'internshipsGrid', 'hackathonsGrid', 'fellowshipsGrid', 'certificationsTimeline', 'skillGapContent', 'reportContent'].forEach((id) => {
      document.getElementById(id).innerHTML = '';
    });
    btnDownload.classList.add('hidden');
    showSection('profile');
    updateNavActive(document.querySelector('[data-section="profile"]'));
    showToast('Form cleared.', 'info');
  }

  // --- Event Bindings ---

  btnMatch.addEventListener('click', matchOpportunities);
  btnReport.addEventListener('click', generateCareerReport);
  btnClear.addEventListener('click', clearForm);
  btnDownload.addEventListener('click', downloadReport);

  // Initialize with profile section
  showSection('profile');
})();
