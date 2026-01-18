"use client";

import { useState, useEffect } from "react";
import Title from "./components/title";
import Info from "./components/info";
import MathBackground from "./components/math-background";
import { Archivo } from "next/font/google";

const archivo = Archivo({ subsets: ["latin"] });

export default function Home() {
  const [showOwlMessage, setShowOwlMessage] = useState(false);
  const [owlClicked, setOwlClicked] = useState(false);

  const handleOwlClick = () => {
    if (!owlClicked) {
      setShowOwlMessage(true);
      setOwlClicked(true);
    }
  };

  useEffect(() => {
    const handleClickOutside = () => {
      setShowOwlMessage(false);
    };

    if (showOwlMessage) {
      document.addEventListener("click", handleClickOutside);
      return () => document.removeEventListener("click", handleClickOutside);
    }
  }, [showOwlMessage]);

  return (
    <main
      className="paper min-h-screen"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 16,
        position: "relative",
        zIndex: 1,
      }}
    >
      <MathBackground />
      <Title onOwlClick={handleOwlClick} />
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: "calc(100vh - 400px)",
          textAlign: "center",
          height: 68,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          pointerEvents: "none",
        }}
      >
        {showOwlMessage && (
          <div
            className={archivo.className}
            style={{
              fontSize: 18,
              color: "#000000",
              opacity: 0,
              animation: "fadeInQuick 2.4s ease forwards",
              pointerEvents: "auto",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            Watching your reasoning, not your answers.
          </div>
        )}
      </div>
      <Info
        title="Upload your math problems. Perch will help you through them."
        blurb="Perch watches your reasoning and offers guidance as you work."
        imageSrc="/dashboard.png"
        imageAlt="Perch dashboard"
      />
      <Info
        title="Learn by doing, not by copying."
        blurb="When Perch spots a mistake, it guides you back on track without just giving the answer. You work through the problem, understand the concept, and own the solution."
        imageSrc="/problem.png"
        imageAlt="Perch problem solving"
      />
      <style>{`
        @keyframes fadeInQuick {
          to { opacity: 0.45; }
        }
      `}</style>
    </main>
  );
}
