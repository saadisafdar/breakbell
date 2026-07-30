/**
 * BreakBell Landing Page Interactions & Dynamics
 */

document.addEventListener('DOMContentLoaded', () => {
  // ── Tab Switching Logic ──
  const tabBtns = document.querySelectorAll('.tab-btn');
  const showcaseViews = document.querySelectorAll('.showcase-view');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetView = btn.getAttribute('data-tab');

      // Deactivate all tabs
      tabBtns.forEach(b => b.classList.remove('active'));
      showcaseViews.forEach(v => v.style.display = 'none');

      // Activate clicked tab
      btn.classList.add('active');
      const activeElement = document.getElementById(`view-${targetView}`);
      if (activeElement) {
        activeElement.style.display = 'block';
      }
    });
  });

  // ── Copy Command Button ──
  const copyBtn = document.getElementById('copy-pip-btn');
  const copyText = document.getElementById('pip-command-text');

  if (copyBtn && copyText) {
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(copyText.innerText.trim()).then(() => {
        const originalIcon = copyBtn.innerHTML;
        copyBtn.innerHTML = '✓ Copied!';
        copyBtn.style.color = '#1F9FBC';
        setTimeout(() => {
          copyBtn.innerHTML = originalIcon;
          copyBtn.style.color = '';
        }, 2000);
      }).catch(err => {
        console.error('Failed to copy: ', err);
      });
    });
  }

  // ── Smooth Scroll for Navigation ──
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        targetElement.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });

  // ── Dynamic Latest Release from GitHub API ──
  const GITHUB_REPO = 'saadisafdar/breakbell';
  const API_URL = `https://api.github.com/repos/${GITHUB_REPO}/releases/latest`;
  const RELEASES_PAGE = `https://github.com/${GITHUB_REPO}/releases`;

  /**
   * Given a release object from the GitHub API, find an asset URL whose
   * filename matches a given pattern (case-insensitive).
   * Falls back to the releases page if no match is found.
   */
  function findAssetUrl(release, pattern) {
    const asset = (release.assets || []).find(a =>
      pattern.test(a.name)
    );
    return asset ? asset.browser_download_url : RELEASES_PAGE;
  }

  fetch(API_URL)
    .then(res => {
      if (!res.ok) throw new Error(`GitHub API responded with ${res.status}`);
      return res.json();
    })
    .then(release => {
      const tag = release.tag_name || '';          // e.g. "v1.2.0"
      const versionLabel = tag || 'Latest';

      // Installer (.exe) asset URL
      const exeUrl = findAssetUrl(release, /\.exe$/i);
      // Portable zip asset URL
      const zipUrl = findAssetUrl(release, /\.zip$/i);

      // ── Update hero badge ──
      const heroBadge = document.getElementById('hero-version-badge');
      if (heroBadge) heroBadge.textContent = `${versionLabel} Released`;

      // ── Update downloads section heading tag ──
      const dlVersionTag = document.getElementById('dl-version-tag');
      if (dlVersionTag) dlVersionTag.textContent = `(${versionLabel})`;

      // ── Wire up hero CTA buttons ──
      const btnHeroExe = document.getElementById('btn-hero-exe');
      if (btnHeroExe) btnHeroExe.href = exeUrl;

      const btnHeroZip = document.getElementById('btn-hero-zip');
      if (btnHeroZip) btnHeroZip.href = zipUrl;

      // ── Wire up download-card buttons ──
      const dlInstaller = document.getElementById('dl-installer');
      if (dlInstaller) dlInstaller.href = exeUrl;

      const dlZip = document.getElementById('dl-zip');
      if (dlZip) dlZip.href = zipUrl;
    })
    .catch(err => {
      // Silently fall back — all links already point to the GitHub releases page
      console.warn('Could not fetch latest release info:', err.message);
    });
});
