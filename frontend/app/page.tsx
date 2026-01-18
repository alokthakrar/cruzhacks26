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
        title="See your work, understand your thinking"
        blurb="Perch reads your handwritten math step by step, understanding not just what you wrote but why. Get feedback in real-time on your work as you solve."
        imageSrc="/mockup.svg"
        imageAlt="Perch dashboard mockup"
      />
      <Info
        title="Learn by doing, not by copying"
        blurb="When Perch spots a mistake, it guides you back on track without just giving the answer. You work through the problem, understand the concept, and own the solution."
        imageSrc="/mockup.svg"
        imageAlt="Perch dashboard mockup"
      />
    </main>
  );
}
