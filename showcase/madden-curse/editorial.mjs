import { EDITORIAL_DETAIL as TUNING } from './constants-playback.mjs';
import { COPY } from './content.mjs';

export async function loadEdition() {
  const response = await fetch('./edition.json');
  if (!response.ok) throw new Error('Edition unavailable');
  const edition = await response.json();
  if (edition.season !== TUNING.season || edition.through !== TUNING.through || edition.teams?.length !== TUNING.teamCount ||
      new Set(edition.teams.map(team => team.id)).size !== TUNING.teamCount ||
      edition.teams.some(team => !Number.isInteger(team.id) || !team.name || !team.headline || !team.article ||
        !/^\.\.\/\.\.\/avatars\/yahoo\/\d+\.webp$/.test(team.avatar))) throw new Error('Invalid edition');
  return edition;
}

function text(tag, value, className) {
  const element = document.createElement(tag);
  element.textContent = value;
  if (className) element.className = className;
  return element;
}

export function report(edition) {
  const root = document.querySelector('[data-report]');
  root.append(text('h2', edition.title), text('p', edition.intro, 'report-lede'));
  const links = document.createElement('nav');
  links.setAttribute('aria-label', COPY.teamLinks);
  edition.teams.forEach(team => {
    const link = text('a', team.name); link.href = `#team-${team.id}`; links.append(link);
    const article = document.createElement('article'); article.id = `team-${team.id}`;
    const image = document.createElement('img'); image.src = team.avatar; image.alt = ''; image.loading = 'lazy';
    article.append(image, text('h3', team.name), text('h4', team.headline), text('p', team.article));
    root.append(article);
  });
  root.insertBefore(links, root.children[2]);
  root.append(text('p', edition.source, 'report-source'));
}

export function story(moment, edition) {
  const overlay = document.querySelector('[data-story]');
  const team = edition?.teams[moment.teamIndex];
  overlay.hidden = !['cold', 'team', 'final'].includes(moment.chapter);
  overlay.dataset.kind = moment.chapter;
  overlay.querySelector('[data-story-name]').textContent = team?.name || (moment.chapter === 'final' ? COPY.leagueName : '');
  overlay.querySelector('[data-story-title]').textContent = team?.headline || COPY[moment.chapter === 'cold' ? 'coldOpen' : 'finalTitle'];
  overlay.querySelector('[data-story-player]').textContent = team?.featured.name || '';
}

export function readTeam(id) {
  if (window.parent !== window) window.parent.postMessage({type: 'madden-report', team: id}, location.origin);
  else {
    const target = document.getElementById(id ? `team-${id}` : 'report');
    target?.scrollIntoView({behavior: 'instant'});
    target?.setAttribute('tabindex', '-1'); target?.focus({preventScroll: true});
  }
}
