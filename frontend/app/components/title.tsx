"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Archivo } from "next/font/google";
import Image from "next/image";

const archivo = Archivo({ subsets: ["latin"] });

type Letter = { id: string; d: string };

export default function Title({ onOwlClick }: { onOwlClick: () => void }) {
  const router = useRouter();
  // Put ONE outlined path per letter here (from Figma export)
  const letters: Letter[] = [
    {
      id: "p",
      d: "M93.0176 123.047L92.041 132.69C89.5182 157.918 80.4036 179.484 64.6973 197.388C48.9909 215.291 31.3314 224.243 11.7188 224.243C7.64974 224.243 3.74349 223.755 0 222.778L17.7002 205.2C22.3389 206.584 26.7334 207.275 30.8838 207.275C55.1351 207.275 69.1325 188.395 72.876 150.635L85.5713 24.0479C81.7464 26.8962 77.6367 30.1921 73.2422 33.9355C67.8711 38.4928 63.151 42.0736 59.082 44.6777L60.0586 34.9121C73.8118 26.7741 88.9079 15.1367 105.347 0L99.7314 56.5186C108.358 41.3818 118.042 28.9714 128.784 19.2871C139.526 9.60286 148.966 4.76074 157.104 4.76074C168.823 4.76074 174.683 14.7705 174.683 34.79C174.683 58.6344 166.992 79.3457 151.611 96.9238C136.23 114.421 118.083 123.169 97.168 123.169L93.0176 123.047ZM94.8486 104.858C101.44 109.009 108.887 111.084 117.188 111.084C128.337 111.084 137.37 104.574 144.287 91.5527C151.286 78.5319 154.785 61.6455 154.785 40.8936C154.785 28.7679 151.489 22.7051 144.897 22.7051C137.655 22.7051 129.069 28.2389 119.141 39.3066C105.876 54.0365 98.2259 71.4925 96.1914 91.6748L94.8486 104.858Z",
    },
    {
      id: "e",
      d: "M74.585 78.0029C76.6195 79.3864 77.6367 81.014 77.6367 82.8857C77.6367 85.4085 75.0326 89.7217 69.8242 95.8252C55.9082 111.938 42.1549 119.995 28.5645 119.995C20.2637 119.995 13.4277 116.699 8.05664 110.107C2.68555 103.516 0 95.0928 0 84.8389C0 66.2842 6.9987 47.526 20.9961 28.5645C35.0749 9.52148 48.9909 0 62.7441 0C72.6725 0 77.6367 5.3304 77.6367 15.9912C77.6367 27.9541 71.818 39.6322 60.1807 51.0254C48.6247 62.4186 34.5052 70.3532 17.8223 74.8291C19.4499 94.4417 27.181 104.248 41.0156 104.248C54.6875 104.248 65.8773 95.4997 74.585 78.0029ZM18.3105 59.9365C20.6706 60.7503 22.8271 61.1572 24.7803 61.1572C34.8714 61.1572 43.7012 58.0648 51.2695 51.8799C58.8379 45.695 62.6221 38.4521 62.6221 30.1514C62.6221 20.6299 57.7799 15.8691 48.0957 15.8691C41.097 15.8691 34.7493 20.0602 29.0527 28.4424C23.4375 36.7432 19.8568 47.2412 18.3105 59.9365Z",
    },
    {
      id: "r",
      d: "M41.2645 51.3916C59.3309 17.1305 77.1124 0 94.6092 0C99.1665 0 103.724 1.05794 108.281 3.17383L91.0691 21.9727C88.465 20.5078 85.1284 19.7754 81.0594 19.7754C72.5958 19.7754 63.644 26.652 54.2039 40.4053C44.8452 54.0771 39.352 68.3187 37.7244 83.1299L34.4285 112.915L16.3621 119.019L16.7283 115.356L17.5828 107.422L18.5594 99.4873L24.907 41.3818L25.6395 35.0342C26.2091 30.2327 26.494 26.3265 26.494 23.3154C26.494 18.3512 25.1105 15.8691 22.3436 15.8691C15.8331 15.8691 9.36342 22.8271 2.93438 36.7432C0.899877 35.1969 -0.0766852 33.61 0.00469501 31.9824C0.248836 27.0182 4.76544 20.4671 13.5545 12.3291C22.4249 4.1097 29.4236 0 34.5506 0C41.4679 0 44.9266 4.55729 44.9266 13.6719C44.9266 15.8691 44.7231 18.8395 44.3162 22.583L43.4617 31.1279L42.3631 41.3818L41.2645 51.3916Z",
    },
    {
      id: "c",
      d: "M85.4492 3.17383L71.5332 19.8975C65.0228 17.2119 58.7972 15.8691 52.8564 15.8691C42.1956 15.8691 33.7728 20.3857 27.5879 29.4189C21.4844 38.4521 18.4326 50.8219 18.4326 66.5283C18.4326 77.596 20.6299 86.5072 25.0244 93.2617C29.5003 100.016 35.319 103.394 42.4805 103.394C54.6061 103.394 64.1276 95.459 71.0449 79.5898C72.8353 81.543 73.7305 83.374 73.7305 85.083C73.7305 91.8376 68.4408 99.3652 57.8613 107.666C47.3633 115.885 37.7197 119.995 28.9307 119.995C20.4671 119.995 13.5091 116.618 8.05664 109.863C2.68555 103.027 0 94.1976 0 83.374C0 62.2965 7.16146 43.1315 21.4844 25.8789C35.8073 8.6263 51.7171 0 69.2139 0C75.5615 0 80.9733 1.05794 85.4492 3.17383Z",
    },
    {
      id: "h",
      d: "M25.1465 148.804C34.668 134.481 45.1253 122.681 56.5186 113.403C67.9932 104.045 77.7995 99.3652 85.9375 99.3652C93.8314 99.3652 97.7783 104.858 97.7783 115.845C97.7783 119.1 97.29 124.105 96.3135 130.859L89.8438 176.392C88.5417 185.506 87.8906 192.708 87.8906 197.998C87.8906 202.23 89.0299 204.346 91.3086 204.346C96.9238 204.346 103.8 196.859 111.938 181.885C113.973 183.105 114.99 184.367 114.99 185.669C114.99 190.959 110.433 197.917 101.318 206.543C92.2852 215.088 84.9202 219.36 79.2236 219.36C72.876 219.36 69.7021 214.803 69.7021 205.688C69.7021 199.015 70.5566 189.779 72.2656 177.979L76.416 148.438C77.7995 138.753 78.4912 131.063 78.4912 125.366C78.4912 119.1 76.2533 115.967 71.7773 115.967C61.3607 115.967 50.8219 123.047 40.1611 137.207C29.5003 151.286 23.234 166.423 21.3623 182.617L18.1885 211.914L0 219.36L0.366211 215.942L1.34277 206.909L2.31934 198.364L14.1602 91.4307C17.0085 66.2028 26.3672 44.6777 42.2363 26.8555C58.1055 8.95182 75.8464 0 95.459 0C99.528 0 103.475 0.447591 107.3 1.34277L89.3555 18.9209C84.7168 17.5374 80.3223 16.8457 76.1719 16.8457C52.002 16.8457 37.8011 35.7259 33.5693 73.4863L25.1465 148.804Z",
    },
  ];

  return (
    <main
      style={{
        minHeight: "calc(100vh - 320px)", // raise the next section higher
        display: "grid",
        placeItems: "center",
        padding: 24,
      }}
    >
      <div style={{ textAlign: "center", marginTop: "-40px" }}>
        <Handwrite word={letters} />
        <p
          className={archivo.className}
          style={{
            fontSize: 18,
            color: "#000000",
            margin: "-40px 0 0 0",
            opacity: 0,
            animation: "fadeIn 0.6s ease forwards",
            animationDelay: "1.2s",
            //transform: "translateX(20px)",
          }}
        >
          A wiser eye on your work
        </p>
        <button
          className={archivo.className}
          style={{
            marginTop: 32,
            padding: "10px 28px",
            fontSize: 16,
            fontWeight: 500,
            backgroundColor: "transparent",
            color: "rgba(0, 0, 0, 0.7)",
            border: "1px solid rgba(0, 0, 0, 0.8)",
            borderRadius: 999,
            cursor: "pointer",
            opacity: 0,
            animation: "fadeIn 0.6s ease forwards",
            animationDelay: "1.4s",
            transition: "all 0.2s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = "rgba(0, 0, 0, 0.9)";
            e.currentTarget.style.backgroundColor = "rgba(0, 0, 0, 0.08)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = "rgba(0, 0, 0, 0.8)";
            e.currentTarget.style.backgroundColor = "transparent";
          }}
          onClick={() => router.push("/dashboard")}
        >
          Start solving →
        </button>
      </div>
      <Image
        src="/owlsticker.png"
        alt="Owl sticker"
        width={200}
        height={250}
        style={{
          position: "fixed",
          bottom: 40,
          right: 40,
          filter: "drop-shadow(2px 2px 4px rgba(0, 0, 0, 0.15))",
          cursor: "pointer",
          transition: "transform 0.2s ease",
        }}
        onMouseEnter={(e) => {
          (e.target as HTMLElement).style.transform = "scale(1.05)";
        }}
        onMouseLeave={(e) => {
          (e.target as HTMLElement).style.transform = "scale(1)";
        }}
        onClick={(e) => {
          e.stopPropagation();
          onOwlClick();
        }}
      />
    </main>
  );
}

function Handwrite({ word }: { word: Letter[] }) {
  const svgRef = useRef<SVGSVGElement | null>(null);

  // Tweak these
  const secondsPerLetter = 0.4;
  const gapBetweenLetters = -0.2;

  // Custom x-positions for each letter (p, e, r, c, h)
  const letterPositions = [100, 270, 350, 430, 510];
  const letterYPositions = [100, 100, 100, 100, 0];

  useEffect(() => {
    const easing = "cubic-bezier(0.55, 0.05, 0.25, 0.95)";
    const svg = svgRef.current;
    if (!svg) return;

    // These are the animated strokes INSIDE the masks
    const maskStrokes = Array.from(
      svg.querySelectorAll<SVGPathElement>("path[data-mask-stroke='true']"),
    );

    let delay = 0;
    for (const p of maskStrokes) {
      const len = p.getTotalLength();
      p.style.strokeDasharray = `${len}`;
      p.style.strokeDashoffset = `${len}`;
      p.style.animation = `draw ${secondsPerLetter}s ${easing} forwards`;
      p.style.animationDelay = `${delay}s`;

      delay += secondsPerLetter + gapBetweenLetters;
    }
  }, []);

  return (
    <svg
      ref={svgRef}
      viewBox="0 0 1200 320"
      width="min(900px, 92vw)"
      height="auto"
      style={{ overflow: "visible" }}
    >
      <defs>
        {/* Optional: tiny blur makes it feel more like ink */}
        <filter id="ink">
          <feGaussianBlur stdDeviation="0.25" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>

        {/* One mask per letter */}
        {word.map((L) => (
          <mask key={L.id} id={`mask-${L.id}`} maskUnits="userSpaceOnUse">
            {/* Black hides everything by default */}
            <rect x="0" y="0" width="1200" height="320" fill="black" />
            {/* White stroke reveals the fill exactly where the “pen” travels */}
            <path
              d={L.d}
              fill="none"
              stroke="white"
              strokeWidth="28"
              strokeLinecap="round"
              strokeLinejoin="round"
              data-mask-stroke="true"
            />
          </mask>
        ))}
      </defs>

      {/* Render the filled letters, each revealed by its own animated mask */}
      <g transform="translate(220, 0)">
        <g filter="url(#ink)">
          {word.map((L, i) => (
            <g
              key={L.id}
              transform={`translate(${letterPositions[i]}, ${letterYPositions[i]})`}
            >
              <path d={L.d} fill="black" mask={`url(#mask-${L.id})`} />
            </g>
          ))}
        </g>
      </g>

      <style>{`
        @keyframes draw {
          to { stroke-dashoffset: 0; }
        }
        @keyframes fadeIn {
          to { opacity: 1; }
        }
      `}</style>
    </svg>
  );
}
