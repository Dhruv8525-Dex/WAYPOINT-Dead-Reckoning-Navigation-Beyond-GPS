import {useEffect, useRef} from 'react';
import type {CSSProperties} from 'react';
import {Link} from 'react-router-dom';
import {Navigation, ArrowUpRight, ArrowRight, Radio, Smartphone, Activity, Route, Database, FlaskConical, FileChartColumn, ShieldCheck} from 'lucide-react';

const workflow = [
  {n:'01', icon:Smartphone, title:'Capture the movement.', text:'Record acceleration, rotation, and GPS with your Android phone. Or bring an existing IO-VNBD journey into your workspace.'},
  {n:'02', icon:Radio, title:'Take away the signal.', text:'Choose when GPS disappears. Compare inertial integration, Kalman filtering, and your trained velocity model.'},
  {n:'03', icon:Route, title:'See what holds course.', text:'Follow the estimated routes, measure drift against recorded GPS, and keep a reproducible report of every experiment.'},
];

export default function Landing() {
  const siteRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const site = siteRef.current;
    if (!site || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    site.classList.add('motion-ready');
    const reveals = Array.from(site.querySelectorAll<HTMLElement>('[data-reveal]'));
    let frame = 0;
    const updateMotion = () => {
      frame = 0;
      const progress = Math.min(window.scrollY, window.innerHeight * 1.4);
      site.style.setProperty('--terrain-shift', `${progress * 0.1}px`);
      site.style.setProperty('--card-shift', `${progress * -0.035}px`);
      reveals.forEach((element) => {
        const bounds = element.getBoundingClientRect();
        const wasVisible = element.classList.contains('is-visible');
        const inView = wasVisible
          ? bounds.bottom > window.innerHeight * -0.18 && bounds.top < window.innerHeight * 1.18
          : bounds.bottom > window.innerHeight * 0.05 && bounds.top < window.innerHeight * 0.92;
        element.classList.toggle('is-visible', inView);
      });
    };
    const onScroll = () => {
      if (!frame) frame = window.requestAnimationFrame(updateMotion);
    };
    updateMotion();
    window.addEventListener('scroll', onScroll, {passive: true});
    window.addEventListener('resize', onScroll);
    return () => {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, []);

  return <div className="terrain-site" ref={siteRef}>
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="terrain-header">
      <Link to="/" className="terrain-brand" aria-label="Waypoint home"><Navigation size={25}/>waypoint<span>.</span></Link>
      <nav aria-label="Website navigation"><a href="#workflow">How it works</a><Link to="/app/docs">Field guide</Link><Link className="terrain-button pale compact" to="/app">Open workspace <ArrowUpRight size={16}/></Link></nav>
    </header>
    <main id="main">
      <section className="terrain-hero" aria-labelledby="hero-title">
        <div className="hero-topline"><span><i/> NAVIGATION BEYOND GPS</span><span>SMARTPHONE INERTIAL RESEARCH / 01</span></div>
        <div className="terrain-hero-grid">
          <div className="terrain-hero-copy"><p className="terrain-kicker">The signal is only the beginning.</p><h1 id="hero-title">Keep your<br/><span>direction.</span></h1><p className="terrain-lead">When GPS fades, motion leaves a trail.<br/>Explore how smartphone sensors can carry a journey forward.</p><div className="terrain-actions"><Link className="terrain-button pale" to="/app">Enter your workspace <ArrowUpRight size={19}/></Link><a className="terrain-text-link" href="#workflow">Explore the process <ArrowRight size={16}/></a></div></div>
          <div className="terrain-instrument" role="img" aria-label="Illustrative terrain route continuing through a simulated GPS outage">
            <div className="instrument-back back-one"/><div className="instrument-back back-two"/>
            <div className="instrument-face"><div className="instrument-heading"><span><Navigation size={16}/> FIELD NOTES</span><span>WP / 001</span></div><div className="instrument-map"><svg viewBox="0 0 400 320" aria-hidden="true"><path className="route-reference" d="M48 266 C70 220 162 286 158 192 S257 186 247 122 S305 108 347 40"/><path className="route-estimate" d="M48 266 C70 220 162 286 158 192 S257 186 247 122"/><circle cx="48" cy="266" r="5" fill="#e0eccb"/><circle className="route-halo" cx="247" cy="122" r="20"/><circle cx="247" cy="122" r="6" fill="#d2e6a9"/></svg><span className="map-axis">MOTION → POSITION</span><div className="instrument-pin"><Radio size={14}/> Beyond the signal</div></div><div className="instrument-bottom"><span>GPS OUTAGE<span className="instrument-value">A new way forward.</span></span><span className="instrument-status">ILLUSTRATIVE<br/>TRAJECTORY</span></div></div>
          </div>
        </div>
        <div className="terrain-hero-bottom"><span>REAL MOTION. MEASURED POSSIBILITIES.</span><a href="#workflow">Discover Waypoint <span>↓</span></a><span>BUILT TO EXPLORE</span></div>
      </section>
      <div className="terrain-principles" data-reveal="fade"><span><Smartphone size={17}/> Your phone is the sensor.</span><span><ShieldCheck size={17}/> Your computer is the lab.</span><span><Activity size={17}/> Every result leaves evidence.</span></div>
      <section className="terrain-workflow" id="workflow"><div className="terrain-section-head" data-reveal="up"><span className="terrain-kicker">01 / FROM MOTION TO MEANING</span><h2>Lose the signal.<br/><span>Find the insight.</span></h2><p>A workspace for asking better navigation questions—and answering them with real recordings.</p></div><div className="terrain-workflow-grid" data-reveal="up">{workflow.map(({n,icon:Icon,title,text}, index)=><article key={n} style={{'--reveal-order': index} as CSSProperties}><div className="workflow-icon"><Icon size={28} strokeWidth={1.3}/><span>{n}</span></div><h3>{title}</h3><p>{text}</p></article>)}</div></section>
      <section className="terrain-tools" aria-labelledby="tools-title"><div className="terrain-tools-art" data-reveal="left"><span className="terrain-kicker">A CLEARER PICTURE OF THE JOURNEY</span><div className="field-stack" aria-hidden="true"><div className="field-sheet sheet-three"><Activity size={34}/><span>Measured evidence</span></div><div className="field-sheet sheet-two"><Route size={34}/><span>Estimated trajectory</span></div><div className="field-sheet sheet-one"><Database size={34}/><span>Original recording</span></div></div><p>From raw movement<br/>to a traceable result.</p><span className="terrain-art-caption">CAPTURE / COMPARE / UNDERSTAND</span></div><div className="terrain-tools-copy" data-reveal="right"><span className="terrain-kicker">02 / YOUR FIELD EQUIPMENT</span><h2 id="tools-title">Everything for<br/>the next discovery.</h2><p>Keep your source data, models, and experiments connected in one local workspace.</p><div className="terrain-tool-links">{[{icon:Database,title:'Recording library',desc:'Import, inspect, and calibrate your sensor data.',to:'/app/datasets'},{icon:FlaskConical,title:'Model workshop',desc:'Train velocity models with separate evaluation data.',to:'/app/models'},{icon:FileChartColumn,title:'Experiment explorer',desc:'Compare routes, inspect errors, export the evidence.',to:'/app/experiments'}].map(({icon:Icon,title,desc,to}, index)=><Link to={to} key={to} style={{'--reveal-order': index} as CSSProperties}><Icon size={23} strokeWidth={1.4}/><span><strong>{title}</strong><small>{desc}</small></span><ArrowUpRight size={19}/></Link>)}</div><Link className="terrain-text-link dark" to="/app/docs">Read the research guide <ArrowRight size={16}/></Link></div></section>
      <section className="terrain-invitation"><div data-reveal="up"><span className="terrain-kicker">THE NEXT JOURNEY STARTS HERE</span><h2>A lab on your laptop.<br/>A world to explore.</h2><p>No account required. Your recordings, experiments, and models live in your local workspace.</p><Link className="terrain-button pale" to="/app/projects">Create your first project <ArrowUpRight size={18}/></Link></div></section>
    </main>
    <footer className="terrain-footer"><div className="terrain-footer-top"><Link to="/" className="terrain-brand"><Navigation size={21}/>waypoint.</Link><span>Navigation beyond GPS.</span><a href="#main" aria-label="Back to top" className="back-top"><ArrowUpRight size={24}/></a></div><nav aria-label="Footer navigation"><Link to="/app">Workspace</Link><Link to="/app/datasets">Recordings</Link><Link to="/app/devices">Phone recorder</Link><a href="#workflow">How it works</a><Link to="/app/docs">Documentation</Link></nav><div className="terrain-wordmark" aria-hidden="true">waypoint.</div><div className="terrain-footer-bottom"><span>A research tool. Accuracy is measured, never assumed.</span><span>LOCAL FIRST / BUILT TO EXPLORE</span></div></footer>
  </div>;
}
