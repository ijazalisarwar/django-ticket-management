import ComingSoon from "@/pages/ComingSoon";
import "bootstrap/dist/css/bootstrap.min.css";
import styles from "./page.module.css";

export default function Home() {
  return (
    <main className={styles.backgroundImageStyle}>
      <ComingSoon />
    </main>
  );
}
