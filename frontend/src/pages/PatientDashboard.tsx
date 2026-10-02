import { useEffect, useRef, useState } from "react";
import { Brain, Check, Clock3, Flame, Footprints, Gamepad2, HeartPulse, Maximize2, Minimize2, Play, RotateCcw } from "lucide-react";
import RoleSwitcher from "../components/RoleSwitcher";
import { completeRoutineItem, getPatientWorkspace, recordGameResult } from "../api/client";

const objects = ["🍎", "🔑", "☂️", "🐱", "📚", "⭐"];
const levels = [3, 4, 5, 6];

export default function PatientDashboard() {
  const [workspaceLoaded, setWorkspaceLoaded] = useState(false);
  const [gameState, setGameState] = useState<"ready" | "watching" | "answering" | "complete">("ready");
  const [level, setLevel] = useState(1);
  const [roundObjects, setRoundObjects] = useState<string[]>([]);
  const [routineItems, setRoutineItems] = useState<Array<{ id: number; time: string; icon: string; title: string; detail: string; completed: number }>>([]);
  const [weeklySummary, setWeeklySummary] = useState({ brain_activities: 0, games: 0, movement: 0, routine_days: 0 });
  const [fullscreen, setFullscreen] = useState(false);
  const gameRef = useRef<HTMLElement>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [score, setScore] = useState(0);

  useEffect(() => {
    getPatientWorkspace().then((data) => { setRoutineItems(data.routine); setWeeklySummary(data.weekly_summary as typeof weeklySummary); setWorkspaceLoaded(true); }).catch(() => setWorkspaceLoaded(false));
  }, []);

  useEffect(() => {
    if (gameState !== "watching") return;
    const timer = window.setTimeout(() => setGameState("answering"), 3500);
    return () => window.clearTimeout(timer);
  }, [gameState]);

  useEffect(() => {
    const syncFullscreen = () => setFullscreen(document.fullscreenElement === gameRef.current);
    document.addEventListener("fullscreenchange", syncFullscreen);
    return () => document.removeEventListener("fullscreenchange", syncFullscreen);
  }, []);

  const startGame = async () => {
    const shuffled = [...objects].sort(() => Math.random() - 0.5);
    setRoundObjects(shuffled.slice(0, levels[level - 1]));
    setSelected([]); setScore(0); setGameState("watching");
    try { await gameRef.current?.requestFullscreen(); setFullscreen(true); } catch { setFullscreen(false); }
  };
  const exitGame = async () => {
    if (document.fullscreenElement) await document.exitFullscreen();
    setFullscreen(false);
    setGameState("ready");
  };
  const submitGame = () => {
    const target = roundObjects;
    const result = selected.filter((item) => target.includes(item)).length;
    setScore(result);
    void recordGameResult(`Object Recall - Level ${level}`, result, target.length);
    if (result === target.length && level < levels.length) setLevel((current) => current + 1);
    if (result !== target.length) setLevel(1);
    setGameState("complete");
  };
  const completeRoutine = async (itemId: number) => {
    await completeRoutineItem(itemId);
    setRoutineItems((items) => items.map((item) => item.id === itemId ? { ...item, completed: 1 } : item));
    setWeeklySummary((summary) => ({ ...summary, routine_days: summary.routine_days + 1 }));
  };

  return <div className="wellbeing-page">
    <header className="wellbeing-header">
      <div className="wellbeing-brand"><div className="wellbeing-brand-mark"><Brain /></div><div><strong>NeuroTrace</strong><span>My wellbeing space</span></div></div>
      <RoleSwitcher role="patient" />
    </header>
    <main className="wellbeing-content">
      <section className="wellbeing-welcome"><div><span className="wellbeing-eyebrow">GOOD MORNING</span><h1>Small steps, every day.</h1><p>Your activities are here to support your routine, memory, and wellbeing.</p></div><div className="streak-chip"><Flame /> 4 day streak{workspaceLoaded ? " · Connected" : ""}</div></section>
      <section className="patient-grid">
         <article ref={gameRef} className={`wellbeing-card memory-card ${fullscreen ? "memory-game-fullscreen" : ""}`}><div className="card-heading"><div><span className="wellbeing-eyebrow">MEMORY GAMES</span><h2>Object Recall</h2></div><div className="game-heading-actions"><Gamepad2 />{gameState !== "ready" && <button className="icon-button" onClick={exitGame} aria-label="Exit full screen">{fullscreen ? <Minimize2 /> : <span>×</span>}</button>}</div></div><p className="card-intro">Remember the objects, then choose the ones you saw.</p>
           {gameState === "ready" && <><div className="difficulty-row"><span>Level {level}</span><span>{levels[level - 1]} objects to remember</span></div><button className="wellbeing-button" onClick={startGame}><Play /> Start Level {level}</button></>}
           {gameState === "watching" && <><div className="object-display">{roundObjects.map((item) => <span key={item}>{item}</span>)}</div><p className="game-hint">Remember these objects... they will disappear soon.</p></>}
           {gameState === "answering" && <><div className="object-options">{[...objects].sort(() => Math.random() - 0.5).map((item) => <button className={selected.includes(item) ? "object-option selected" : "object-option"} key={item} onClick={() => setSelected((current) => current.includes(item) ? current.filter((value) => value !== item) : [...current, item])}>{item}</button>)}</div><button className="wellbeing-button" onClick={submitGame}>Check answers <Check /></button></>}
           {gameState === "complete" && <div className="game-result"><span className="result-icon"><Check /></span><div><strong>{score === roundObjects.length ? (level > 1 ? `Level ${level - 1} complete!` : "Nice work!") : "Back to Level 1"}</strong><p>You remembered {score} of {roundObjects.length} objects.{score === roundObjects.length && level <= levels.length ? ` Level ${level} is ready.` : " Try again from Level 1 to continue."}</p></div><button className="icon-button" onClick={startGame} aria-label="Continue game">{score === roundObjects.length ? <Play /> : <RotateCcw />}</button></div>}
        </article>
         <article className="wellbeing-card progress-card"><div className="card-heading"><div><span className="wellbeing-eyebrow">YOUR WEEK</span><h2>Patient progress</h2></div><HeartPulse /></div><div className="progress-stats"><div><Brain /><strong>{weeklySummary.brain_activities}</strong><span>Brain activities</span></div><div><Gamepad2 /><strong>{weeklySummary.games}</strong><span>Games</span></div><div><Footprints /><strong>{weeklySummary.movement}</strong><span>Movement</span></div><div><Clock3 /><strong>{weeklySummary.routine_days}</strong><span>Routine days</span></div></div><div className="encouragement"><span>🌱</span><div><strong>Great job!</strong><p>The goal is staying engaged, not getting a score.</p></div></div></article>
      </section>
       <section className="wellbeing-card routine-card"><div className="card-heading"><div><span className="wellbeing-eyebrow">MY DAILY ROUTINE</span><h2>Today at a glance</h2></div><span className="routine-date">{new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" })}</span></div><div className="routine-list">{routineItems.map((item, index) => <div className={index === 2 ? "routine-item current" : "routine-item"} key={item.id}><time>{item.time}</time><span className="routine-icon">{item.icon}</span><div><strong>{item.title}</strong><p>{item.detail}</p></div>{item.completed ? <Check className="routine-check" /> : <button className="routine-complete" onClick={() => void completeRoutine(item.id)}>Mark done</button>}</div>)}</div></section>
    </main>
  </div>;
}
