import React from 'react';

export type CompanionState = 'idle' | 'listening' | 'thinking' | 'speaking';

interface CompanionAvatarProps {
  state: CompanionState;
  onClick?: () => void;
}

/** KRITAM companion portrait: original vector illustration with a dimensional, polished finish. */
export const CompanionAvatar: React.FC<CompanionAvatarProps> = ({ state, onClick }) => {
  const active = state !== 'idle';
  return (
    <button
      type="button"
      className={`kritam-agent kritam-agent--${state}`}
      onClick={onClick}
      title={`KRITAM assistant — ${state}`}
      aria-label={`KRITAM assistant, ${state}`}
    >
      <svg className="kritam-agent__portrait" viewBox="0 0 96 96" role="img" aria-hidden="true">
        <defs>
          <radialGradient id="agent-backdrop" cx="35%" cy="22%" r="90%">
            <stop offset="0" stopColor="#555d91"/><stop offset=".55" stopColor="#252b49"/><stop offset="1" stopColor="#101522"/>
          </radialGradient>
          <linearGradient id="agent-rim" x1="0" y1="0" x2="1" y2="1">
            <stop stopColor="#d5c5ff"/><stop offset=".48" stopColor="#8870ff"/><stop offset="1" stopColor="#51c9ee"/>
          </linearGradient>
          <linearGradient id="agent-hair" x1="0" y1="0" x2="1" y2="1">
            <stop stopColor="#44445f"/><stop offset=".5" stopColor="#171927"/><stop offset="1" stopColor="#080b13"/>
          </linearGradient>
          <linearGradient id="agent-skin" x1="0" y1="0" x2=".9" y2="1">
            <stop stopColor="#ffe0ca"/><stop offset="1" stopColor="#c98778"/>
          </linearGradient>
          <linearGradient id="agent-jacket" x1="0" y1="0" x2="1" y2="1">
            <stop stopColor="#353d59"/><stop offset="1" stopColor="#121827"/>
          </linearGradient>
          <clipPath id="agent-clip"><circle cx="48" cy="48" r="44"/></clipPath>
        </defs>
        <circle cx="48" cy="48" r="47" fill="url(#agent-rim)"/>
        <circle cx="48" cy="48" r="44.5" fill="url(#agent-backdrop)"/>
        <g clipPath="url(#agent-clip)">
          <ellipse cx="48" cy="100" rx="43" ry="39" fill="#0b0e18"/>
          <path d="M7 100 Q9 68 30 64 L65 62 Q89 70 91 100Z" fill="url(#agent-jacket)"/>
          <path d="M36 61h24v17q-11 12-24 0Z" fill="url(#agent-skin)"/>
          <path d="M26 31Q27 8 50 10Q75 10 74 38L70 60Q62 73 49 73Q31 70 26 52Z" fill="url(#agent-hair)"/>
          <path d="M30 39Q31 23 45 21Q60 19 68 34L66 55Q62 66 49 67Q36 65 31 53Z" fill="url(#agent-skin)"/>
          <path d="M27 43Q22 20 42 12Q63 4 74 28L68 43Q65 29 53 26Q43 35 29 35Z" fill="url(#agent-hair)"/>
          <path d="M31 34Q26 47 32 59L27 52Q20 34 27 22Z" fill="#202337"/>
          <path d="M64 31Q74 43 66 60L71 54Q78 36 68 24Z" fill="#171a2b"/>
          <path d="M35 43q5-4 10 0" fill="none" stroke="#49302e" strokeWidth="2" strokeLinecap="round"/>
          <path d="M51 43q5-4 10 0" fill="none" stroke="#49302e" strokeWidth="2" strokeLinecap="round"/>
          <ellipse cx="40" cy="47" rx="3" ry="3.5" fill="#28253a"/><ellipse cx="56" cy="47" rx="3" ry="3.5" fill="#28253a"/>
          <circle cx="41" cy="46" r="1" fill="#fff"/><circle cx="57" cy="46" r="1" fill="#fff"/>
          <path d="M48 47l-2 8 4 1" fill="none" stroke="#b9766a" strokeWidth="1.3" strokeLinecap="round"/>
          <path d="M42 59q6 5 12 0" fill="none" stroke="#914e55" strokeWidth="1.8" strokeLinecap="round"/>
          <path d="M30 40q-8 1-5 11q2 6 7 2" fill="url(#agent-skin)" stroke="#252b48" strokeWidth="2"/>
          <circle cx="28" cy="48" r="7" fill="#202943" stroke="#a58aff" strokeWidth="2"/>
          <circle cx="28" cy="48" r="3.5" fill="#9c8bff"/><circle cx="28" cy="48" r="1.4" fill="#f3efff"/>
          <path d="M29 54q-2 7 6 8" fill="none" stroke="#b6a4ff" strokeWidth="1.5" strokeLinecap="round"/>
          <circle cx="35" cy="63" r="2" fill="#c7bcff"/>
          <path d="M31 69l17 17 18-17 11 31H19Z" fill="url(#agent-jacket)"/>
          <path d="M38 67l10 11 10-11-2 25H40Z" fill="#171c2c"/>
          <path d="M24 80l8-7 8 21" fill="none" stroke="#7c72c8" strokeWidth="1.5" opacity=".9"/>
          <path d="M72 80l-8-7-8 21" fill="none" stroke="#7c72c8" strokeWidth="1.5" opacity=".9"/>
          <circle cx="70" cy="73" r="2.5" fill="#a99aff"/><path d="M70 68v-3m0 16v-3m-5-5h-3m16 0h-3" stroke="#a99aff" strokeWidth="1" opacity=".85"/>
        </g>
        <circle cx="48" cy="48" r="44.5" fill="none" stroke="#ffffff" strokeOpacity=".24"/>
      </svg>
      {active && <span className="kritam-agent__status" aria-hidden="true" />}
    </button>
  );
};
