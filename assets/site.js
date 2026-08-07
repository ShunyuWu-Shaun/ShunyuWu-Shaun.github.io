(() => {
  const root = document.documentElement;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const splash = document.querySelector("[data-site-splash]");

  if (splash) {
    let seen = false;
    try {
      seen = sessionStorage.getItem("sw-site-intro") === "seen";
    } catch (_) {
      seen = false;
    }

    if (seen || reduceMotion) {
      splash.remove();
    } else {
      root.classList.add("intro-playing");
      window.setTimeout(() => {
        splash.classList.add("splash-exit");
        root.classList.remove("intro-playing");
        try {
          sessionStorage.setItem("sw-site-intro", "seen");
        } catch (_) {
          // The animation still works when storage is unavailable.
        }
      }, 1650);
      window.setTimeout(() => splash.remove(), 2450);
    }
  }

  const revealTargets = document.querySelectorAll("[data-reveal]");
  if (reduceMotion || !("IntersectionObserver" in window)) {
    revealTargets.forEach((target) => target.classList.add("is-visible"));
  } else {
    const revealObserver = new IntersectionObserver(
      (entries, observer) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.12 }
    );
    revealTargets.forEach((target) => revealObserver.observe(target));
  }

  const hero = document.querySelector(".home-hero");
  const lattice = document.querySelector(".hero-lattice");
  if (hero && lattice && !reduceMotion && window.matchMedia("(pointer: fine)").matches) {
    hero.addEventListener("pointermove", (event) => {
      const bounds = hero.getBoundingClientRect();
      const x = (event.clientX - bounds.left) / bounds.width - 0.5;
      const y = (event.clientY - bounds.top) / bounds.height - 0.5;
      lattice.style.setProperty("--shift-x", `${x * 13}px`);
      lattice.style.setProperty("--shift-y", `${y * 9}px`);
    });
    hero.addEventListener("pointerleave", () => {
      lattice.style.setProperty("--shift-x", "0px");
      lattice.style.setProperty("--shift-y", "0px");
    });
  }
})();
