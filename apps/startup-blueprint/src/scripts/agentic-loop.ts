type LoopStep = {
  id: string;
  title: string;
  label: string;
  summary: string;
};

const steps: LoopStep[] = [
  {
    id: 'human-steering',
    title: 'Human Steering',
    label: 'Direction',
    summary:
      'Humans decide direction and priorities. AI executes the work you choose.',
  },
  {
    id: 'agent-input',
    title: 'Agent Input',
    label: 'Perplexity Claude',
    summary:
      'Perplexity, OpenCode, and Claude follow shared instructions and standards.',
  },
  {
    id: 'git-commit',
    title: 'Git Commit',
    label: 'Audit Trail',
    summary:
      'Every change lands as a commit, capturing intent and audit history.',
  },
  {
    id: 'ci-gates',
    title: 'CI Gates',
    label: 'Guardrails',
    summary:
      'Environment checks, labels, and formatting keep the pipeline consistent.',
  },
  {
    id: 'docs-checks',
    title: 'Docs Checks',
    label: 'Business Docs',
    summary:
      'Business docs are validated alongside code with link checks and linting.',
  },
  {
    id: 'tests-builds',
    title: 'Tests and Builds',
    label: 'Workspaces',
    summary: 'Workspaces run targeted tests and builds only when needed.',
  },
  {
    id: 'deploy',
    title: 'Preview or Prod',
    label: 'Deploy',
    summary: 'Preview deploys on PRs, production deploys on main merges.',
  },
  {
    id: 'crewai-base',
    title: 'CrewAI Base Review',
    label: 'Diff + Logs',
    summary:
      'Always reviews the diff plus CI logs to suggest fixes and auto-debug.',
  },
  {
    id: 'crewai-router',
    title: 'CrewAI Router',
    label: 'Multi-Voice',
    summary:
      'Routes deeper reviews: quick, full, legal, and future marketing or board.',
  },
];

const LOOP_ID = 'agentic-loop';
const SVG_ID = 'agentic-loop-svg';
const CENTER_ID = 'agentic-loop-center';
const DETAILS_ID = 'agentic-loop-details';

const activeClass = 'ring-2 ring-indigo-500 shadow-xl';

const createSvgCircle = (
  svg: SVGSVGElement,
  radius: number,
  centerX: number,
  centerY: number
) => {
  const circle = document.createElementNS(
    'http://www.w3.org/2000/svg',
    'circle'
  );
  const circumference = 2 * Math.PI * radius;

  circle.setAttribute('cx', centerX.toString());
  circle.setAttribute('cy', centerY.toString());
  circle.setAttribute('r', radius.toString());
  circle.setAttribute('fill', 'none');
  circle.setAttribute('stroke', '#6366f1');
  circle.setAttribute('stroke-width', '2');
  circle.setAttribute('stroke-dasharray', circumference.toString());
  circle.setAttribute('stroke-dashoffset', circumference.toString());
  circle.setAttribute('stroke-linecap', 'round');
  circle.setAttribute('opacity', '0.5');

  svg.appendChild(circle);
  return { circle, circumference };
};

const animateCircle = (circle: SVGCircleElement, circumference: number) => {
  const duration = 1200;
  const start = performance.now();

  const tick = (now: number) => {
    const progress = Math.min((now - start) / duration, 1);
    const offset = circumference * (1 - progress);
    circle.setAttribute('stroke-dashoffset', offset.toString());
    if (progress < 1) {
      requestAnimationFrame(tick);
    }
  };

  requestAnimationFrame(tick);
};

const updateDetails = (
  step: LoopStep,
  center: HTMLElement,
  details: HTMLElement
) => {
  const titleEl = center.querySelector<HTMLElement>('[data-loop-title]');
  const summaryEl = center.querySelector<HTMLElement>('[data-loop-summary]');
  const detailTitle = details.querySelector<HTMLElement>(
    '[data-loop-detail-title]'
  );
  const detailSummary = details.querySelector<HTMLElement>(
    '[data-loop-detail-summary]'
  );

  if (titleEl) titleEl.textContent = step.title;
  if (summaryEl) summaryEl.textContent = step.summary;
  if (detailTitle) detailTitle.textContent = step.title;
  if (detailSummary) detailSummary.textContent = step.summary;
};

const setActive = (
  step: LoopStep,
  nodes: Map<string, HTMLButtonElement>,
  center: HTMLElement,
  details: HTMLElement
) => {
  nodes.forEach((node, id) => {
    if (id === step.id) {
      node.classList.add(...activeClass.split(' '));
      node.setAttribute('aria-pressed', 'true');
    } else {
      node.classList.remove(...activeClass.split(' '));
      node.setAttribute('aria-pressed', 'false');
    }
  });
  updateDetails(step, center, details);
};

const initLoop = () => {
  const loop = document.getElementById(LOOP_ID);
  const svg = document.getElementById(SVG_ID) as SVGSVGElement | null;
  const center = document.getElementById(CENTER_ID);
  const details = document.getElementById(DETAILS_ID);

  if (!loop || !svg || !center || !details) return;

  const rect = loop.getBoundingClientRect();
  const size = Math.min(rect.width, rect.height);
  const radius = size / 2 - 90;
  const centerX = size / 2;
  const centerY = size / 2;
  const stepAngle = (Math.PI * 2) / steps.length;

  svg.setAttribute('viewBox', `0 0 ${size} ${size}`);
  const { circle, circumference } = createSvgCircle(
    svg,
    radius,
    centerX,
    centerY
  );
  animateCircle(circle, circumference);

  const nodes = new Map<string, HTMLButtonElement>();

  steps.forEach((step, index) => {
    const angle = -Math.PI / 2 + index * stepAngle;
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);

    const node = document.createElement('button');
    node.type = 'button';
    node.className =
      'agentic-loop-node absolute flex h-24 w-24 flex-col items-center justify-center rounded-full border border-indigo-200 bg-white text-center text-xs font-semibold text-gray-900 shadow-md transition duration-300 hover:-translate-y-1 hover:shadow-lg focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2';
    node.style.left = `${x}px`;
    node.style.top = `${y}px`;
    node.style.transform = 'translate(-50%, -50%)';
    node.setAttribute('aria-pressed', 'false');
    node.setAttribute('aria-label', `${step.title}. ${step.summary}`);
    node.innerHTML = `
      <span class="text-[0.65rem] uppercase tracking-[0.08em] text-indigo-500">
        ${step.label}
      </span>
      <span class="mt-1 text-xs font-semibold text-gray-900">
        ${step.title}
      </span>
    `;

    node.addEventListener('mouseenter', () =>
      setActive(step, nodes, center, details)
    );
    node.addEventListener('focus', () =>
      setActive(step, nodes, center, details)
    );

    loop.appendChild(node);
    nodes.set(step.id, node);
  });

  setActive(steps[0], nodes, center, details);
};

document.addEventListener('DOMContentLoaded', initLoop);
