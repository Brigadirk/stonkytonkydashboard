import { useEffect, useRef } from 'react';
import { GPU_COLORS } from './gpuPrices';
import type { GpuType } from './gpuPrices';
import { GPU_PROFILES, GPU_PROFILE_REVIEWED, GPU_SUPPORT_SOURCE } from './gpuProfiles';

export default function GpuDetails({ gpu, onClose }: { gpu: GpuType; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  // Capture before showModal moves focus; keep it across Strict Mode effects.
  const opener = useRef(document.activeElement as HTMLElement | null);
  const profile = GPU_PROFILES[gpu];
  useEffect(() => {
    const element = ref.current;
    const previousOverflow = document.body.style.overflow;
    if (element && !element.open) element.showModal();
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = previousOverflow; if (!element?.isConnected) opener.current?.focus(); };
  }, []);
  return <dialog ref={ref} className="gpu-dialog" aria-labelledby="gpu-profile-title" aria-describedby="gpu-profile-summary" onCancel={event => { event.preventDefault(); onClose(); }} onClose={onClose} onClick={event => {
    if (event.target !== event.currentTarget) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) onClose();
  }}>
    <div className="gpu-dialog-header"><span className="gpu-kicker">GPU FIELD GUIDE</span><button onClick={onClose} aria-label="Close GPU details">✕</button></div>
    <span className="gpu-model-category"><i style={{ background: GPU_COLORS[gpu] }}/>{profile.category}</span>
    <h2 id="gpu-profile-title">{gpu}<span>.</span></h2>
    <p id="gpu-profile-summary" className="gpu-profile-summary">{profile.summary}</p>
    <div className="gpu-profile-facts"><div><span>Introduced</span><strong>{profile.introduced.slice(0, 4)}</strong></div><div><span>Architecture</span><strong>{profile.architecture}</strong></div><div><span>CUDA support</span><strong className="gpu-support-status">Ongoing*</strong></div></div>
    <section className="gpu-profile-section"><h3>Typical uses</h3><ul>{profile.uses.map(use => <li key={use}>{use}</li>)}</ul><a href={profile.source} target="_blank" rel="noreferrer">NVIDIA announcement & model context ↗</a></section>
    <section className="gpu-profile-section"><h3>Launch and availability</h3><p>{profile.availability}</p></section>
    <section className="gpu-lifetime"><h3>Expected life & end of life</h3><p><strong>Hardware retirement date: unknown.</strong> The sources reviewed do not state a fixed hardware lifetime or a retirement date for this model.</p><p><strong>Useful life: no estimate assigned.</strong> For a rental operator, this depends on the workload, power costs, maintenance, and software support. This is operating context, not a manufacturer lifetime forecast.</p><p>*NVIDIA lists ongoing CUDA toolkit and driver support for {profile.architecture}. This does not guarantee a specific number of years of remaining hardware life. <a href={GPU_SUPPORT_SOURCE} target="_blank" rel="noreferrer">NVIDIA support matrix ↗</a></p></section>
    <footer className="gpu-dialog-footer"><span>Sources checked {GPU_PROFILE_REVIEWED} · Model facts are separate from rental price data.</span><button onClick={onClose}>Back to prices</button></footer>
  </dialog>;
}
