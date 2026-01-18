import Title from "./components/title";
import Info from "./components/info";

export default function Home() {
  return (
    <main
      className="paper min-h-screen"
      style={{ display: "flex", flexDirection: "column", gap: 16 }}
    >
      <Title />
      <Info
        title="Solve while you think"
        blurb="It watches how you solve problems and offers guidance as you work — not after you’re stuck.

        Perch adjusts difficulty in real time and helps students stay in flow without giving away answers."
        imageSrc="/mockup.svg"
        imageAlt="Perch dashboard mockup"
      />
    </main>
  );
}
