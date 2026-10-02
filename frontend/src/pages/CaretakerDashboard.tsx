import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { AlertTriangle, Bell, CalendarCheck, CheckCircle2, ChevronRight, HeartHandshake, MessageCircle, Phone, Plus, Send, ShieldCheck, UserRound, X } from "lucide-react";
import RoleSwitcher from "../components/RoleSwitcher";
import { api, getCaretakerWorkspace, type CaretakerWorkspace } from "../api/client";

export default function CaretakerDashboard() {
  const [workspace, setWorkspace] = useState<CaretakerWorkspace | null>(null);
  const [showContactForm, setShowContactForm] = useState(false);
  const [contactError, setContactError] = useState("");
  const [savingContact, setSavingContact] = useState(false);
  const [contact, setContact] = useState({ name: "", phone: "", detail: "Family support", kind: "family" });
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");
  const [chatMessages, setChatMessages] = useState<Array<{ role: "user" | "assistant"; content: string }>>([
    { role: "assistant", content: "Hello. I can help you think through care routines, reminders, and questions to discuss with the care team." },
  ]);

  useEffect(() => { getCaretakerWorkspace().then(setWorkspace).catch(() => setWorkspace(null)); }, []);
  const followUp = async (id: number) => {
    await api.post(`/care/caretaker/medications/${id}/follow-up`);
    setWorkspace((current) => current ? { ...current, medications: current.medications.map((item) => item.id === id ? { ...item, status: "follow_up", detail: "Follow-up requested" } : item) } : current);
  };
  const addContact = async (event: FormEvent) => {
    event.preventDefault();
    setContactError("");
    setSavingContact(true);
    try {
      const response = await api.post("/care/caretaker/contacts", contact);
      setWorkspace((current) => current ? { ...current, contacts: [...current.contacts, response.data] } : current);
      setContact({ name: "", phone: "", detail: "Family support", kind: "family" });
      setShowContactForm(false);
    } catch (error: any) {
      setContactError(error?.response?.data?.detail ?? "Could not save contact. Restart the backend and try again.");
    } finally {
      setSavingContact(false);
    }
  };
  const doctor = workspace?.contacts.find((item) => item.kind === "doctor");
  const family = workspace?.contacts.find((item) => item.kind === "family");
  const whatsappLink = (phone?: string) => phone ? `https://wa.me/${phone.replace(/\D/g, "")}` : undefined;
  const sendChatMessage = async (event: FormEvent) => {
    event.preventDefault();
    const content = chatInput.trim();
    if (!content || chatLoading) return;
    const nextMessages = [...chatMessages, { role: "user" as const, content }];
    setChatMessages(nextMessages);
    setChatInput("");
    setChatError("");
    setChatLoading(true);
    try {
      const response = await api.post<{ message: string }>("/caretaker/chat", { messages: nextMessages });
      setChatMessages([...nextMessages, { role: "assistant", content: response.data.message }]);
    } catch (error: any) {
      setChatError(error?.response?.data?.detail ?? "The care assistant is unavailable right now.");
    } finally {
      setChatLoading(false);
    }
  };
  return <div className="wellbeing-page caretaker-page">
    <header className="wellbeing-header"><div className="wellbeing-brand"><div className="wellbeing-brand-mark caretaker-mark"><HeartHandshake /></div><div><strong>NeuroTrace</strong><span>Caretaker space</span></div></div><RoleSwitcher role="caretaker" /></header>
    <main className="wellbeing-content">
      <section className="wellbeing-welcome"><div><span className="wellbeing-eyebrow">CARETAKER DASHBOARD</span><h1>Supporting Margaret, together.</h1><p>Stay close to the daily details that help care feel calm and consistent.</p></div><div className="connected-chip"><span /> {workspace ? "Patient connected" : "Connecting..."}</div></section>
      <section className="caretaker-grid">
        <article className="wellbeing-card medication-card"><div className="card-heading"><div><span className="wellbeing-eyebrow">MEDICATION FOLLOW-UP</span><h2>Today's medicines</h2></div><Bell /></div>{workspace?.medications.map((item) => <div className="medication-row" key={item.id}><div className="medication-time">{item.time}</div><div><strong>{item.title}</strong><p>{item.detail}</p></div>{item.status === "done" ? <CheckCircle2 className="done-icon" /> : <button className="small-action" onClick={() => void followUp(item.id)}>Mark follow-up</button>}</div>)}</article>
        <article className="wellbeing-card safety-card"><div className="card-heading"><div><span className="wellbeing-eyebrow">PRECAUTIONS &amp; SAFETY</span><h2>Safety check</h2></div><ShieldCheck /></div><div className="safety-status"><ShieldCheck /><div><strong>{workspace?.safety.status === "clear" ? "All clear today" : "Review needed"}</strong><p>{workspace?.safety.message ?? "Loading safety status..."}</p></div></div><button className="text-action">Review safety guidance <ChevronRight /></button></article>
        <article className="wellbeing-card contact-card"><div className="card-heading"><div><span className="wellbeing-eyebrow">DOCTOR CONTACT</span><h2>Care team</h2></div><UserRound /></div><div className="doctor-person"><div className="avatar">DR</div><div><strong>{doctor?.name ?? "Care team"}</strong><p>{doctor?.detail ?? "Contact unavailable"}</p></div>{doctor?.phone && <a className="circle-action" href={`tel:${doctor.phone}`} aria-label="Call doctor"><Phone /></a>}</div><a className="wellbeing-button light" href={doctor?.phone ? `sms:${doctor.phone}` : undefined}>Message care team</a></article>
        <article className="wellbeing-card emergency-card"><div className="card-heading"><div><span className="wellbeing-eyebrow">SUPPORT / EMERGENCY CONTACTS</span><h2>Help when you need it</h2></div><AlertTriangle /></div><p>Save trusted mobile numbers so calls can be placed directly from this dashboard.</p><div className="emergency-actions"><a className="emergency-button" href="tel:112"><Phone /> Emergency services <strong>112</strong></a>{family?.phone && <a className="support-button" href={whatsappLink(family.phone)}><Phone /> WhatsApp {family.name} <strong>Call</strong></a>}<button className="support-button" onClick={() => { setContactError(""); setShowContactForm(true); }}><Plus /> Add contact</button></div>{showContactForm && <form className="contact-form" onSubmit={(event) => void addContact(event)}><div className="contact-form-header"><strong>Add support contact</strong><button type="button" onClick={() => setShowContactForm(false)}><X /></button></div><input required placeholder="Name" value={contact.name} onChange={(event) => setContact({ ...contact, name: event.target.value })} /><input required placeholder="Mobile number" type="tel" value={contact.phone} onChange={(event) => setContact({ ...contact, phone: event.target.value })} /><input required placeholder="Relationship or detail" value={contact.detail} onChange={(event) => setContact({ ...contact, detail: event.target.value })} />{contactError && <div className="contact-error">{contactError}</div>}<button className="wellbeing-button" type="submit" disabled={savingContact}>{savingContact ? "Saving..." : "Save contact"}</button></form>}</article>
      </section>
      <section className="care-note"><CalendarCheck /><div><strong>Next care review</strong><span>{workspace?.next_review ?? "Loading review schedule..."}</span></div></section>
     </main>
     <button className={`caretaker-chat-launcher${chatOpen ? " is-open" : ""}`} onClick={() => setChatOpen((open) => !open)} aria-label={chatOpen ? "Close care assistant" : "Open care assistant"}><MessageCircle /><span>{chatOpen ? "Close" : "Care assistant"}</span></button>
     {chatOpen && <aside className="caretaker-chat-panel" aria-label="NeuroTrace care assistant">
       <div className="caretaker-chat-header"><div><span className="wellbeing-eyebrow">NEUROTRACE SUPPORT</span><strong>Care assistant</strong><small>For guidance, not diagnosis</small></div><button type="button" onClick={() => setChatOpen(false)} aria-label="Close"><X /></button></div>
       <div className="caretaker-chat-messages">{chatMessages.map((message, index) => <div className={`caretaker-chat-message ${message.role}`} key={`${message.role}-${index}`}>{message.content}</div>)}{chatLoading && <div className="caretaker-chat-message assistant">Thinking...</div>}</div>
       {chatError && <div className="caretaker-chat-error">{chatError}</div>}
       <form className="caretaker-chat-form" onSubmit={(event) => void sendChatMessage(event)}><input value={chatInput} onChange={(event) => setChatInput(event.target.value)} placeholder="Ask about care support..." aria-label="Message care assistant" /><button type="submit" disabled={chatLoading || !chatInput.trim()} aria-label="Send message"><Send /></button></form>
     </aside>}
   </div>;
}
