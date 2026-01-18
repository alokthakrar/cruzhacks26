"use client";

import Image from "next/image";
import { Archivo } from "next/font/google";

const archivo = Archivo({ subsets: ["latin"] });

export type InfoProps = {
  title: string;
  blurb: string;
  imageSrc: string; // e.g. "/mockup.png" in public/
  imageAlt: string;
  reversed?: boolean; // flip layout left/right
};

export default function Info({ title, blurb, imageSrc, imageAlt, reversed = false }: InfoProps) {
  return (
    <section
      className={archivo.className}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "20px",
        alignItems: "center",
        padding: "48px 24px",
        maxWidth: 840,
        margin: "0 auto",
        opacity: 0,
        animation: "fadeIn 0.6s ease forwards",
        animationDelay: "2.0s",
      }}
    >
      <div style={{ order: reversed ? 2 : 1, textAlign: "center" }}>
        <h2 style={{ margin: "0 0 12px 0", fontSize: "28px", fontWeight: 600 }}>
          {title}
        </h2>
        <p style={{ margin: 0, lineHeight: 1.6, color: "#333" }}>{blurb}</p>
      </div>

      <div style={{ order: reversed ? 1 : 2, textAlign: "center", width: "100%", marginTop: 12 }}>
        <Image
          src={imageSrc}
          alt={imageAlt}
          width={640}
          height={400}
          style={{
            width: "100%",
            height: "auto",
            borderRadius: 12,
            boxShadow: "0 16px 32px rgba(0,0,0,0.15)",
            border: "1px solid rgba(0, 0, 0, 0.8)",
          }}
          priority
        />
      </div>
      <style>{`
        @keyframes fadeIn {
          to { opacity: 1; }
        }
      `}</style>
    </section>
  );
}
