/* ==========================================================================
   ALEXANDRIA STUDIO • AI ACADEMIC & ENGINEERING STUDY STUDIO JAVASCRIPT
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  initAmbientCanvas();
  initModelDropdown();
  initGuiAgentControls();
  initUsageModal();
  initSubjectChips();
  initCustomSubjectModal();
  initBookshelf();
  initForm();
  initModal();
});

// State
let currentPackage = null;
let selectedModel = "google/gemini-3.8-flash";
let selectedSubject = "AUTO";
let customSubjectName = "";
let isGuiAgentActive = false;
let selectedGuiTarget = "perplexity";
let isGuiVisible = true;

// Authoritative reference mapping for academic disciplines
const SUBJECT_TEXTBOOKS = {
  "AUTO": "Authoritative Academic & University References (Auto-Detect)",
  "CS_AI": "Stuart Russell, Peter Norvig & Gary Bradski (AI & Computer Vision)",
  "MATHS": "B.S. Grewal & Erwin Kreyszig (Higher Engineering Mathematics)",
  "PHYSICS": "David Halliday & Robert Resnick (Fundamentals of Physics)",
  "ELECTRICAL": "Robert Boylestad & B.L. Theraja (Circuit Theory & Electrical)",
  "MECHANICAL": "Beer & Johnston / N.D. Bhatt (Engineering Mechanics & Graphics)",
  "CUSTOM": "Custom Academic Reference"
};

/* --------------------------------------------------------------------------
   1. AMBIENT PARTICLES CANVAS
   -------------------------------------------------------------------------- */
function initAmbientCanvas() {
  const canvas = document.getElementById("ambient-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener("resize", () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const particles = [];
  const particleCount = 45;

  for (let i = 0; i < particleCount; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      radius: Math.random() * 2 + 0.8,
      speedY: -(Math.random() * 0.4 + 0.15),
      speedX: (Math.random() - 0.5) * 0.3,
      alpha: Math.random() * 0.6 + 0.2,
      pulseSpeed: Math.random() * 0.02 + 0.01,
    });
  }

  function render() {
    ctx.clearRect(0, 0, width, height);

    for (let p of particles) {
      p.y += p.speedY;
      p.x += p.speedX;
      p.alpha += Math.sin(Date.now() * p.pulseSpeed) * 0.005;

      if (p.y < -10) {
        p.y = height + 10;
        p.x = Math.random() * width;
      }
      if (p.x < -10) p.x = width + 10;
      if (p.x > width + 10) p.x = -10;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(245, 158, 11, ${Math.max(0.1, Math.min(0.8, p.alpha))})`;
      ctx.shadowBlur = 10;
      ctx.shadowColor = "rgba(245, 158, 11, 0.6)";
      ctx.fill();
    }

    requestAnimationFrame(render);
  }

  render();
}

/* --------------------------------------------------------------------------
   1.5. HUMAN GUI BROWSER AGENT CONTROLS & 1-CLICK LOGIN SETUP
   -------------------------------------------------------------------------- */
function initGuiAgentControls() {
  const tabApi = document.getElementById("tab-mode-api");
  const tabGui = document.getElementById("tab-mode-gui");
  const guiBar = document.getElementById("gui-agent-bar");
  const targetChips = document.querySelectorAll(".gui-target-chip");
  const visibleToggle = document.getElementById("gui-visible-toggle");

  const loginModal = document.getElementById("gui-login-modal");
  const loginBackdrop = document.getElementById("gui-login-backdrop");
  const btnOpenLogin = document.getElementById("btn-open-login-modal");
  const btnCloseLogin = document.getElementById("btn-close-gui-login");
  const btnDoneLogin = document.getElementById("btn-done-gui-login");
  const btnLaunchClaude = document.getElementById("btn-launch-claude-login");
  const btnLaunchGemini = document.getElementById("btn-launch-gemini-login");
  const loginFeedback = document.getElementById("login-launch-feedback");

  function setEngineMode(isGui) {
    isGuiAgentActive = isGui;
    if (isGui) {
      if (tabGui) tabGui.classList.add("active");
      if (tabApi) tabApi.classList.remove("active");
      if (guiBar) guiBar.classList.remove("hidden");
    } else {
      if (tabApi) tabApi.classList.add("active");
      if (tabGui) tabGui.classList.remove("active");
      if (guiBar) guiBar.classList.add("hidden");
    }
  }

  function setGuiTarget(target) {
    selectedGuiTarget = target;
    targetChips.forEach((c) => {
      if (c.getAttribute("data-target") === target) {
        c.classList.add("active");
      } else {
        c.classList.remove("active");
      }
    });
  }

  if (tabApi) {
    tabApi.addEventListener("click", () => setEngineMode(false));
  }
  if (tabGui) {
    tabGui.addEventListener("click", () => setEngineMode(true));
  }

  targetChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const target = chip.getAttribute("data-target");
      if (target) setGuiTarget(target);
    });
  });

  if (visibleToggle) {
    visibleToggle.addEventListener("change", (e) => {
      isGuiVisible = e.target.checked;
    });
  }

  // Modal open/close
  function openLoginModal() {
    if (loginModal) loginModal.classList.remove("hidden");
    if (loginFeedback) loginFeedback.classList.add("hidden");
  }
  function closeLoginModal() {
    if (loginModal) loginModal.classList.add("hidden");
  }

  if (btnOpenLogin) btnOpenLogin.addEventListener("click", openLoginModal);
  if (btnCloseLogin) btnCloseLogin.addEventListener("click", closeLoginModal);
  if (btnDoneLogin) btnDoneLogin.addEventListener("click", closeLoginModal);
  if (loginBackdrop) loginBackdrop.addEventListener("click", closeLoginModal);

  async function launchLoginBrowser(target) {
    if (loginFeedback) {
      loginFeedback.classList.remove("hidden");
      loginFeedback.innerHTML = `<span>⏳ Launching Google Chrome on desktop for ${target === "claude" ? "Claude AI" : "Gemini"}...</span>`;
    }
    try {
      const res = await fetch("/api/gui-agent/launch-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target })
      });
      if (res.ok) {
        if (loginFeedback) {
          loginFeedback.innerHTML = `<span>✅ <strong>Chrome window opened!</strong> Please log in in the opened Chrome browser. Your session will remain saved permanently.</span>`;
        }
      } else {
        throw new Error("Failed to launch Chrome");
      }
    } catch (err) {
      if (loginFeedback) {
        loginFeedback.innerHTML = `<span style="color: #f87171;">⚠️ Error launching browser: ${err.message}</span>`;
      }
    }
  }

  if (btnLaunchClaude) {
    btnLaunchClaude.addEventListener("click", () => launchLoginBrowser("claude"));
  }
  if (btnLaunchGemini) {
    btnLaunchGemini.addEventListener("click", () => launchLoginBrowser("gemini"));
  }

  // Natural language detection in topic input
  const topicInput = document.getElementById("topic-input");
  if (topicInput) {
    topicInput.addEventListener("input", (e) => {
      const text = e.target.value.toLowerCase();
      if (text.includes("claude")) {
        setEngineMode(true);
        setGuiTarget("claude");
      } else if (text.includes("gemini web") || (text.includes("from gemini") && !text.includes("flash"))) {
        setEngineMode(true);
        setGuiTarget("gemini");
      } else if (text.includes("perplexity") || text.includes("from perplexity")) {
        setEngineMode(true);
        setGuiTarget("perplexity");
      } else if (text.includes("gui agent") || text.includes("browser agent") || text.includes("google search")) {
        setEngineMode(true);
        setGuiTarget("google");
      }
    });
  }
}

/* --------------------------------------------------------------------------
   2. UNDER-CHAT MODEL DROPDOWN & TOKEN USAGE POPUP
   -------------------------------------------------------------------------- */
function initModelDropdown() {
  const triggerBtn = document.getElementById("model-trigger-btn");
  const dropdownMenu = document.getElementById("model-dropdown-menu");
  const wrapper = document.getElementById("model-picker-wrapper");
  const selectedName = document.getElementById("selected-model-name");
  const menuItems = document.querySelectorAll(".model-dropdown-menu .menu-item:not(.menu-usage-item)");
  const usageItem = document.getElementById("btn-view-usage");

  if (!triggerBtn || !dropdownMenu) return;

  function toggleMenu(e) {
    if (e) {
      e.stopPropagation();
      e.preventDefault();
    }
    const isHidden = dropdownMenu.classList.contains("hidden");
    if (isHidden) {
      dropdownMenu.classList.remove("hidden");
      if (wrapper) wrapper.classList.add("open");
    } else {
      dropdownMenu.classList.add("hidden");
      if (wrapper) wrapper.classList.remove("open");
    }
  }

  function closeMenu() {
    dropdownMenu.classList.add("hidden");
    if (wrapper) wrapper.classList.remove("open");
  }

  // Single exclusive click listener on trigger button
  triggerBtn.addEventListener("click", toggleMenu);

  // Close when clicking outside
  document.addEventListener("click", (e) => {
    if (wrapper && !wrapper.contains(e.target)) {
      closeMenu();
    }
  });

  // Close on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeMenu();
    }
  });

  // Model Items click handling
  menuItems.forEach((item) => {
    item.addEventListener("click", (e) => {
      e.stopPropagation();
      const modelId = item.getAttribute("data-model");
      const modelName = item.getAttribute("data-name");

      if (!modelId) return;

      selectedModel = modelId;
      if (selectedName) {
        selectedName.textContent = modelName;
      }

      // Update active checkmarks
      menuItems.forEach((it) => {
        it.classList.remove("active");
        const right = it.querySelector(".item-right");
        if (right) right.innerHTML = '<span class="item-arrow">›</span>';
      });

      item.classList.add("active");
      const activeRight = item.querySelector(".item-right");
      if (activeRight) activeRight.innerHTML = '<span class="item-check">✓</span>';

      // Check quota status (notify student if token quota completed)
      const quotaStatus = item.getAttribute("data-quota");
      const alertBanner = document.getElementById("token-over-limit-alert");
      const alertDesc = document.getElementById("token-alert-desc");

      if (quotaStatus === "completed") {
        if (alertBanner && alertDesc) {
          alertDesc.textContent = `Model ${modelName} Error: Token Quota Completed on OpenRouter (Error 402). You can continue or click 'Switch to Free Engine' below.`;
          alertBanner.classList.remove("hidden");
        }
      } else {
        if (alertBanner) alertBanner.classList.add("hidden");
      }

      closeMenu();
      console.log(`[Alexandria Studio] Active Model Selected: ${selectedModel} (${modelName}, quota: ${quotaStatus})`);
    });
  });

  // View Usage click handling
  if (usageItem) {
    usageItem.addEventListener("click", (e) => {
      e.stopPropagation();
      closeMenu();
      openUsageModal();
    });
  }
}

/* --------------------------------------------------------------------------
   2B. TOKEN USAGE & MODEL LIMIT MONITORING MODAL
   -------------------------------------------------------------------------- */
async function fetchTokenUsage() {
  try {
    const res = await fetch("/api/usage");
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.warn("Could not fetch token usage:", err);
    return null;
  }
}

async function updateUsageUI() {
  const data = await fetchTokenUsage();
  if (!data) return;

  const countNum = document.getElementById("gauge-tokens-num");
  const quotaNum = document.getElementById("gauge-quota-num");
  const meterFill = document.getElementById("usage-meter-fill");
  const pctText = document.getElementById("gauge-percent-text");
  const remText = document.getElementById("gauge-remaining-text");
  const badge = document.getElementById("gauge-status-badge");
  const overLimitBox = document.getElementById("usage-over-limit-box");
  const alertBanner = document.getElementById("token-over-limit-alert");

  if (countNum) countNum.textContent = data.total_tokens.toLocaleString();
  if (quotaNum) quotaNum.textContent = `/ ${data.quota_limit.toLocaleString()} tokens`;
  if (pctText) pctText.textContent = `${data.quota_percentage}% used`;
  if (remText) remText.textContent = `${data.remaining_tokens.toLocaleString()} remaining`;

  if (meterFill) {
    meterFill.style.width = `${Math.min(100, Math.max(2, data.quota_percentage))}%`;
    if (data.quota_percentage >= 80 || data.is_over_limit) {
      meterFill.classList.add("warning");
    } else {
      meterFill.classList.remove("warning");
    }
  }

  if (badge) {
    if (data.is_over_limit) {
      badge.className = "gauge-badge over_limit";
      badge.textContent = "🔴 Quota Over Limit";
    } else {
      badge.className = "gauge-badge healthy";
      badge.textContent = "🟢 Budget Healthy";
    }
  }

  // If over limit, show warnings
  if (data.is_over_limit) {
    if (overLimitBox) overLimitBox.classList.remove("hidden");
    if (alertBanner) alertBanner.classList.remove("hidden");
  } else {
    if (overLimitBox) overLimitBox.classList.add("hidden");
  }
}

function openUsageModal() {
  const modal = document.getElementById("usage-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  updateUsageUI();
}

function closeUsageModal() {
  const modal = document.getElementById("usage-modal");
  if (modal) modal.classList.add("hidden");
}

function switchToFreeModel() {
  selectedModel = "nex-agi/nex-n2.5-mini:free";
  const selectedName = document.getElementById("selected-model-name");
  if (selectedName) selectedName.textContent = "Nex AGI Mini (Free)";

  // Clear checkmarks in model menu and activate Nex AGI Mini
  const menuItems = document.querySelectorAll(".model-dropdown-menu .menu-item");
  menuItems.forEach((it) => {
    if (it.getAttribute("data-model") === "nex-agi/nex-n2.5-mini:free") {
      it.classList.add("active");
      const right = it.querySelector(".item-right");
      if (right) right.innerHTML = '<span class="item-check">✓</span>';
    } else {
      it.classList.remove("active");
      const right = it.querySelector(".item-right");
      if (right) right.innerHTML = '<span class="item-arrow">›</span>';
    }
  });

  // Hide over-limit alerts
  const alertBanner = document.getElementById("token-over-limit-alert");
  const overLimitBox = document.getElementById("usage-over-limit-box");
  if (alertBanner) alertBanner.classList.add("hidden");
  if (overLimitBox) overLimitBox.classList.add("hidden");

  closeUsageModal();
  console.log("[Alexandria Studio] Switched to 100% Free Fast Engine (Nex AGI Mini)");
}

function initUsageModal() {
  const backdrop = document.getElementById("usage-modal-backdrop");
  const closeBtn = document.getElementById("btn-close-usage");
  const dialogClose = document.getElementById("btn-dialog-close");
  const resetBtn = document.getElementById("btn-reset-tokens");
  const switchFreeBtn = document.getElementById("btn-box-switch-free");
  const alertSwitchBtn = document.getElementById("btn-alert-switch-free");
  const alertUsageBtn = document.getElementById("btn-alert-view-usage");
  const alertDismissBtn = document.getElementById("btn-alert-dismiss");

  if (backdrop) backdrop.addEventListener("click", closeUsageModal);
  if (closeBtn) closeBtn.addEventListener("click", closeUsageModal);
  if (dialogClose) dialogClose.addEventListener("click", closeUsageModal);

  if (switchFreeBtn) switchFreeBtn.addEventListener("click", switchToFreeModel);
  if (alertSwitchBtn) alertSwitchBtn.addEventListener("click", switchToFreeModel);

  if (alertUsageBtn) alertUsageBtn.addEventListener("click", openUsageModal);
  if (alertDismissBtn) {
    alertDismissBtn.addEventListener("click", () => {
      const alertBanner = document.getElementById("token-over-limit-alert");
      if (alertBanner) alertBanner.classList.add("hidden");
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener("click", async () => {
      try {
        await fetch("/api/usage/reset", { method: "POST" });
        await updateUsageUI();
      } catch (err) {
        console.error("Could not reset usage:", err);
      }
    });
  }

  // Poll usage initially
  updateUsageUI();
}

function initSubjectChips() {
  const chips = document.querySelectorAll(".subject-chip");
  const textbookLabel = document.getElementById("active-textbook-name");

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const subjectCode = chip.getAttribute("data-subject");
      if (subjectCode === "CUSTOM") {
        openCustomSubjectModal();
        return;
      }

      chips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      selectedSubject = subjectCode;
      
      const textbook = SUBJECT_TEXTBOOKS[selectedSubject] || "Authoritative Academic Literature";
      if (textbookLabel) {
        textbookLabel.textContent = textbook;
      }
      console.log(`[Alexandria Studio] Active Subject: ${selectedSubject} -> ${textbook}`);
    });
  });
}

function openCustomSubjectModal() {
  const modal = document.getElementById("custom-subject-modal");
  const input = document.getElementById("custom-subject-input");
  if (!modal) return;
  modal.classList.remove("hidden");
  if (input) {
    input.value = customSubjectName || "";
    input.focus();
  }
}

function closeCustomSubjectModal() {
  const modal = document.getElementById("custom-subject-modal");
  if (modal) modal.classList.add("hidden");
}

function initCustomSubjectModal() {
  const modal = document.getElementById("custom-subject-modal");
  const backdrop = document.getElementById("custom-modal-backdrop");
  const closeBtn = document.getElementById("btn-close-custom-modal");
  const cancelBtn = document.getElementById("btn-cancel-custom-subject");
  const saveBtn = document.getElementById("btn-save-custom-subject");
  const input = document.getElementById("custom-subject-input");
  const customLabel = document.getElementById("custom-subject-label");
  const textbookLabel = document.getElementById("active-textbook-name");
  const customChip = document.getElementById("btn-custom-subject");
  const chips = document.querySelectorAll(".subject-chip");

  if (backdrop) backdrop.addEventListener("click", closeCustomSubjectModal);
  if (closeBtn) closeBtn.addEventListener("click", closeCustomSubjectModal);
  if (cancelBtn) cancelBtn.addEventListener("click", closeCustomSubjectModal);

  function applyCustom() {
    const val = input ? input.value.trim() : "";
    if (val) {
      customSubjectName = val;
      selectedSubject = val;
      if (customLabel) customLabel.textContent = val;
      if (textbookLabel) textbookLabel.textContent = `Standard Academic Reference (${val})`;
      
      chips.forEach((c) => c.classList.remove("active"));
      if (customChip) customChip.classList.add("active");
      console.log(`[Alexandria Studio] Custom Subject Applied: ${val}`);
    }
    closeCustomSubjectModal();
  }

  if (saveBtn) saveBtn.addEventListener("click", applyCustom);
  if (input) {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        applyCustom();
      } else if (e.key === "Escape") {
        closeCustomSubjectModal();
      }
    });
  }
}

/* --------------------------------------------------------------------------
   3. BOOKSHELF STORAGE & RENDERING
   -------------------------------------------------------------------------- */
async function initBookshelf() {
  try {
    const res = await fetch("/api/history");
    if (res.ok) {
      const history = await res.json();
      renderBooks(history);
    }
  } catch (err) {
    console.warn("Could not load library history:", err);
  }
}

function renderBooks(books) {
  const container = document.getElementById("shelf-books-container");
  const countLabel = document.getElementById("book-count");
  if (!container) return;

  container.innerHTML = "";

  if (!books || books.length === 0) {
    if (countLabel) countLabel.textContent = "0";
    const hint = document.createElement("div");
    hint.className = "book empty-shelf-hint";
    hint.textContent = "Your shelf is waiting for its first study book! Research a topic above.";
    container.appendChild(hint);
    return;
  }

  if (countLabel) countLabel.textContent = books.length;

  books.forEach((book) => {
    const bookEl = createBookElement(book);
    container.appendChild(bookEl);
  });
}

function createBookElement(book) {
  const bookEl = document.createElement("div");
  bookEl.className = "book";
  bookEl.setAttribute("data-id", book.id);
  
  // Natural variations in book height and leather color
  const heightVariation = 175 + (Math.abs(hashString(book.topic)) % 25);
  bookEl.style.height = `${heightVariation}px`;
  bookEl.style.setProperty("--book-color", book.color || "#8B3A3A");

  // Subtle Spine Text
  const spineText = document.createElement("span");
  spineText.className = "spine-text";
  spineText.textContent = book.topic;
  spineText.title = `${book.topic} (${book.subject || 'Engineering'})`;

  // Quick Delete Icon Button on Spine
  const delBtn = document.createElement("button");
  delBtn.className = "book-spine-del";
  delBtn.innerHTML = "✕";
  delBtn.title = "Delete this book";
  delBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    deleteBook(book.id);
  });

  bookEl.appendChild(delBtn);
  bookEl.appendChild(spineText);

  bookEl.addEventListener("click", () => {
    openReadingModal(book);
  });

  return bookEl;
}

async function deleteBook(bookId) {
  if (!bookId) return;
  if (!confirm("Are you sure you want to remove this book from your study shelf?")) {
    return;
  }

  try {
    const res = await fetch(`/api/history/${encodeURIComponent(bookId)}`, {
      method: "DELETE"
    });

    if (res.ok) {
      // Remove from shelf DOM
      const bookEl = document.querySelector(`.book[data-id="${bookId}"]`);
      if (bookEl) bookEl.remove();

      // Update count
      const container = document.getElementById("shelf-books-container");
      const remainingBooks = container.querySelectorAll(".book:not(.empty-shelf-hint)");
      const countLabel = document.getElementById("book-count");
      if (countLabel) countLabel.textContent = remainingBooks.length;

      if (remainingBooks.length === 0) {
        renderBooks([]);
      }

      // Close modal and minimized bar if open
      const modal = document.getElementById("reading-modal");
      const minBar = document.getElementById("minimized-notebook-bar");
      if (currentPackage && currentPackage.id === bookId) {
        modal.classList.add("hidden");
        if (minBar) minBar.classList.add("hidden");
      }
    } else {
      const err = await res.json().catch(() => ({}));
      alert("Could not delete book: " + (err.detail || "Server error"));
    }
  } catch (err) {
    console.error("Delete failed:", err);
    alert("Delete failed: " + err.message);
  }
}

function hashString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return hash;
}

/* --------------------------------------------------------------------------
   4. RESEARCH FORM & ANIMATED STEPPER
   -------------------------------------------------------------------------- */
function initForm() {
  const form = document.getElementById("generate-form");
  const topicInput = document.getElementById("topic-input");
  const generateBtn = document.getElementById("generate-btn");
  const stepper = document.getElementById("research-stepper");
  const briefingCard = document.getElementById("briefing-card");
  const briefingText = document.getElementById("briefing-text");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const topic = topicInput.value.trim();
    if (!topic) return;

    // Collect selected formats
    const checkedBoxes = form.querySelectorAll('input[name="format"]:checked');
    const formats = Array.from(checkedBoxes).map((cb) => cb.value);
    if (formats.length === 0) {
      formats.push("handwritten", "pdf", "docx");
    }

    // UI state: generating
    generateBtn.disabled = true;
    generateBtn.innerHTML = `<span>⏳ Researching...</span>`;
    stepper.classList.remove("hidden");

    // Show Briefing
    if (briefingCard && briefingText) {
      briefingCard.classList.remove("hidden");
      if (isGuiAgentActive) {
        const targetLabels = {
          "all": "All Web Engines (Claude + Gemini + Perplexity)",
          "claude": "Claude AI Web",
          "gemini": "Google Gemini Web",
          "google": "Google Search",
          "perplexity": "Perplexity Web"
        };
        const targetLabel = targetLabels[selectedGuiTarget] || "Perplexity Web";
        briefingText.textContent = `🤖 Human GUI Browser Agent: Querying ${targetLabel} in Chrome to retrieve authoritative academic content...`;
      } else {
        briefingText.textContent = `Analyzing academic literature and citations via ${selectedModel.split('/')[1] || selectedModel}...`;
      }
    }

    // Run animation stepper progression
    const stopStepper = runStepperAnimation(isGuiAgentActive, selectedGuiTarget);

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          model: selectedModel,
          subject: selectedSubject,
          formats,
          gui_agent: isGuiAgentActive,
          gui_target: selectedGuiTarget,
          headless: !isGuiVisible
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Generation failed");
      }

      const studyPackage = await res.json();
      stopStepper(true);

      // Update briefing card with academic briefing
      if (briefingCard && briefingText && studyPackage.briefing) {
        briefingText.textContent = studyPackage.briefing;
      }

      // Add to shelf
      addBookToShelf(studyPackage);

      // Open notes view in White Ruled Notebook
      setTimeout(() => {
        openReadingModal(studyPackage);
        topicInput.value = "";
      }, 600);

    } catch (err) {
      console.error(err);
      stopStepper(false);
      const isTokenErr = /402|budget|credit|afford|token/i.test(err.message);
      if (isTokenErr) {
        const alertBanner = document.getElementById("token-over-limit-alert");
        const alertDesc = document.getElementById("token-alert-desc");
        if (alertBanner) {
          if (alertDesc) alertDesc.textContent = `Model Token Limit Exceeded: ${err.message}. Switch to 100% Free Engine (Nemotron 3.5) with 1 click below.`;
          alertBanner.classList.remove("hidden");
        }
      } else {
        alert("Error generating notes: " + err.message);
      }
    } finally {
      generateBtn.disabled = false;
      generateBtn.innerHTML = `
        <span class="btn-sparkle">✨</span>
        <span class="btn-text">Generate Notes</span>
      `;
      setTimeout(() => {
        stepper.classList.add("hidden");
      }, 2500);
      updateUsageUI();
    }
  });
}

function runStepperAnimation(isGui = false, target = "perplexity") {
  const steps = [
    { id: "step-search", progress: 25 },
    { id: "step-scrape", progress: 50 },
    { id: "step-synthesis", progress: 75 },
    { id: "step-compile", progress: 95 },
  ];

  // Dynamically customize stepper labels based on engine mode
  const searchNode = document.getElementById("step-search");
  const scrapeNode = document.getElementById("step-scrape");
  const synthNode = document.getElementById("step-synthesis");
  const compileNode = document.getElementById("step-compile");

  if (isGui) {
    const targetName = target === "all" ? "All Web Engines" : (target === "claude" ? "Claude AI" : (target === "gemini" ? "Gemini" : (target === "google" ? "Google" : "Perplexity")));
    if (searchNode) {
      const title = searchNode.querySelector(".node-title");
      const desc = searchNode.querySelector(".node-desc");
      if (title) title.textContent = "🖥️ Chrome Session";
      if (desc) desc.textContent = "Launching browser agent";
    }
    if (scrapeNode) {
      const title = scrapeNode.querySelector(".node-title");
      const desc = scrapeNode.querySelector(".node-desc");
      if (title) title.textContent = `🌐 ${targetName} Web`;
      if (desc) desc.textContent = target === "all" ? "Claude, Gemini & Perplexity" : "Navigating & human typing";
    }
    if (synthNode) {
      const title = synthNode.querySelector(".node-title");
      const desc = synthNode.querySelector(".node-desc");
      if (title) title.textContent = "📥 Content Stream";
      if (desc) desc.textContent = "Extracting generated answer";
    }
    if (compileNode) {
      const title = compileNode.querySelector(".node-title");
      const desc = compileNode.querySelector(".node-desc");
      if (title) title.textContent = "📖 Alexandria Synthesis";
      if (desc) desc.textContent = "Compiling notes, DOCX & PDF";
    }
  } else {
    if (searchNode) {
      const title = searchNode.querySelector(".node-title");
      const desc = searchNode.querySelector(".node-desc");
      if (title) title.textContent = "Book Search";
      if (desc) desc.textContent = "Locating reference chapter";
    }
    if (scrapeNode) {
      const title = scrapeNode.querySelector(".node-title");
      const desc = scrapeNode.querySelector(".node-desc");
      if (title) title.textContent = "Fact Checking";
      if (desc) desc.textContent = "Extracting derivations";
    }
    if (synthNode) {
      const title = synthNode.querySelector(".node-title");
      const desc = synthNode.querySelector(".node-desc");
      if (title) title.textContent = "AI Engine";
      if (desc) desc.textContent = "Running Gemini/Claude";
    }
    if (compileNode) {
      const title = compileNode.querySelector(".node-title");
      const desc = compileNode.querySelector(".node-desc");
      if (title) title.textContent = "Handwritten Sheet";
      if (desc) desc.textContent = "Styling notebook & PDF";
    }
  }

  const fill = document.getElementById("progress-bar-fill");
  let currentIdx = 0;

  function setStep(idx) {
    steps.forEach((s, i) => {
      const node = document.getElementById(s.id);
      if (!node) return;
      if (i < idx) {
        node.className = "step-node completed";
      } else if (i === idx) {
        node.className = "step-node active";
      } else {
        node.className = "step-node";
      }
    });
    if (fill && steps[idx]) {
      fill.style.width = `${steps[idx].progress}%`;
    }
  }

  setStep(0);

  const timer = setInterval(() => {
    if (currentIdx < steps.length - 1) {
      currentIdx++;
      setStep(currentIdx);
    }
  }, 2200);

  return function stop(success) {
    clearInterval(timer);
    if (success) {
      steps.forEach((s) => {
        const node = document.getElementById(s.id);
        if (node) node.className = "step-node completed";
      });
      if (fill) fill.style.width = "100%";
    }
  };
}

function addBookToShelf(studyPackage) {
  const container = document.getElementById("shelf-books-container");
  const countLabel = document.getElementById("book-count");
  if (!container) return;

  // Remove empty shelf hint if present
  const hint = container.querySelector(".empty-shelf-hint");
  if (hint) hint.remove();

  const bookEl = createBookElement(studyPackage);
  bookEl.classList.add("active-book");
  container.prepend(bookEl);

  const currentCount = container.querySelectorAll(".book:not(.empty-shelf-hint)").length;
  if (countLabel) countLabel.textContent = currentCount;
}

/* --------------------------------------------------------------------------
   5. HANDWRITTEN NOTEBOOK TAG PARSER (HIGHLIGHTERS & STICKY NOTES)
   -------------------------------------------------------------------------- */
function parseHandwrittenTags(rawMarkdown) {
  if (!rawMarkdown) return "";

  let parsed = rawMarkdown;

  // 0. Strip backticks around all special tags: `[HL: ...]` -> [HL: ...]
  parsed = parsed.replace(/`(\[(?:HL|STICKY_|FORMULA_|FLOW_|MEMORY_)[^`]+\])`/gi, '$1');

  // 1. Highlighters: [HL: yellow | text], [HL: green | text], [HL: pink | text]
  parsed = parsed.replace(/\[HL:\s*yellow\s*\|\s*([^\]]+)\]/gi, '<span class="hl-yellow">$1</span>');
  parsed = parsed.replace(/\[HL:\s*green\s*\|\s*([^\]]+)\]/gi, '<span class="hl-green">$1</span>');
  parsed = parsed.replace(/\[HL:\s*pink\s*\|\s*([^\]]+)\]/gi, '<span class="hl-pink">$1</span>');

  // 2. Post-it Sticky Notes
  // [STICKY_THINK: ...] -> Pastel Pink
  parsed = parsed.replace(/\[STICKY_THINK:\s*([\s\S]*?)\]/gi, (match, content) => {
    return `<div class="sticky-note sticky-think"><div class="sticky-note-header">💡 Think!</div>${content.trim()}</div>`;
  });

  // [STICKY_REMEMBER: ...] -> Pastel Amber
  parsed = parsed.replace(/\[STICKY_REMEMBER:\s*([\s\S]*?)\]/gi, (match, content) => {
    return `<div class="sticky-note sticky-remember"><div class="sticky-note-header">📌 Remember!</div>${content.trim()}</div>`;
  });

  // [STICKY_EXAM: ...] -> Peach / Coral
  parsed = parsed.replace(/\[STICKY_EXAM:\s*([\s\S]*?)\]/gi, (match, content) => {
    return `<div class="sticky-note sticky-exam"><div class="sticky-note-header">🎯 Exam Focus</div>${content.trim()}</div>`;
  });

  // [STICKY_FACT: ...] -> Mint Green
  parsed = parsed.replace(/\[STICKY_FACT:\s*([\s\S]*?)\]/gi, (match, content) => {
    return `<div class="sticky-note sticky-fact"><div class="sticky-note-header">⭐ Amazing Fact</div>${content.trim()}</div>`;
  });

  // 3. Formula Box: [FORMULA_BOX: ... ]
  parsed = parsed.replace(/\[FORMULA_BOX:\s*([\s\S]*?)\]/gi, (match, content) => {
    const formatted = content.trim().replace(/\n/g, '<br>');
    return `<div class="formula-box"><div class="formula-box-title">📐 Formula to Remember</div><div class="formula-content">${formatted}</div></div>`;
  });

  // 4. Memory Trick: [MEMORY_TRICK: ... ]
  parsed = parsed.replace(/\[MEMORY_TRICK:\s*([\s\S]*?)\]/gi, (match, content) => {
    return `<div class="memory-trick-box"><span class="memory-trick-icon">🧠</span><div><strong>MEMORY TRICK:</strong> ${content.trim()}</div></div>`;
  });

  // 5. Flow Steps: [FLOW_STEP: Step 1 -> Step 2 -> ... ]
  parsed = parsed.replace(/\[FLOW_STEP:\s*([^\]]+)\]/gi, (match, content) => {
    const parts = content.split(/->|➔/).map(s => `<span>${s.trim()}</span>`).join(' <span class="flow-step-arrow">➔</span> ');
    return `<div class="flow-step-box">${parts}</div>`;
  });

  // Convert markdown to HTML using marked
  if (typeof marked !== "undefined") {
    return marked.parse(parsed);
  }
  return parsed;
}

/* --------------------------------------------------------------------------
   6. READING MODAL / WHITE RULED NOTEBOOK VIEWER
   -------------------------------------------------------------------------- */
function initModal() {
  const modal = document.getElementById("reading-modal");
  const backdrop = document.getElementById("modal-backdrop");
  const closeBtn = document.getElementById("btn-close-modal");
  const minimizeBtn = document.getElementById("btn-minimize-modal");
  const deleteBtn = document.getElementById("btn-delete-book");
  const copyBtn = document.getElementById("btn-copy-notes");
  const minBar = document.getElementById("minimized-notebook-bar");
  const minBarTrigger = document.getElementById("min-bar-trigger");
  const minExpandBtn = document.getElementById("min-btn-expand");
  const minCloseBtn = document.getElementById("min-btn-close");
  const minTitle = document.getElementById("min-notebook-title");

  function close() {
    modal.classList.add("hidden");
    if (minBar) minBar.classList.add("hidden");
  }

  function minimize() {
    modal.classList.add("hidden");
    if (minBar) {
      if (currentPackage && minTitle) {
        minTitle.textContent = currentPackage.topic;
      }
      minBar.classList.remove("hidden");
    }
  }

  function restore() {
    if (minBar) minBar.classList.add("hidden");
    modal.classList.remove("hidden");
  }

  if (closeBtn) closeBtn.addEventListener("click", close);
  if (backdrop) backdrop.addEventListener("click", close);
  if (minimizeBtn) minimizeBtn.addEventListener("click", minimize);
  if (minBarTrigger) minBarTrigger.addEventListener("click", restore);
  if (minExpandBtn) minExpandBtn.addEventListener("click", restore);
  if (minCloseBtn) minCloseBtn.addEventListener("click", () => {
    if (minBar) minBar.classList.add("hidden");
  });

  if (deleteBtn) {
    deleteBtn.addEventListener("click", () => {
      if (currentPackage && currentPackage.id) {
        deleteBook(currentPackage.id);
        if (minBar) minBar.classList.add("hidden");
      }
    });
  }

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !modal.classList.contains("hidden")) {
      close();
    }
  });

  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      if (currentPackage && currentPackage.notes_markdown) {
        navigator.clipboard.writeText(currentPackage.notes_markdown).then(() => {
          const originalText = copyBtn.innerHTML;
          copyBtn.innerHTML = `<span>✅</span> Copied!`;
          setTimeout(() => {
            copyBtn.innerHTML = originalText;
          }, 2000);
        });
      }
    });
  }
}

function openReadingModal(studyPackage) {
  currentPackage = studyPackage;
  const modal = document.getElementById("reading-modal");
  const minBar = document.getElementById("minimized-notebook-bar");
  if (minBar) minBar.classList.add("hidden");
  
  // Set Topic & Date
  const topicTitle = document.getElementById("modal-topic-title");
  if (topicTitle) topicTitle.textContent = studyPackage.topic;

  const dateLabel = document.getElementById("modal-date");
  if (dateLabel) dateLabel.textContent = studyPackage.created_at || "September 2026";

  const subjectTag = document.getElementById("modal-subject-tag");
  if (subjectTag) subjectTag.textContent = studyPackage.subject || "Engineering Studies";

  const bookTag = document.getElementById("modal-book-tag");
  if (bookTag) bookTag.textContent = studyPackage.target_book || "University Reference";

  // Set Executive Summary
  const summaryBody = document.getElementById("modal-summary-text");
  if (summaryBody) {
    summaryBody.textContent = studyPackage.summary || `Comprehensive revision study sheet prepared for ${studyPackage.topic}.`;
  }

  // Render Handwritten HTML Canvas with Highlighters and Sticky Notes
  const markdownContainer = document.getElementById("modal-markdown-content");
  if (markdownContainer) {
    markdownContainer.innerHTML = parseHandwrittenTags(studyPackage.notes_markdown || "");
    if (typeof renderMathInElement === "function") {
      renderMathInElement(markdownContainer, {
        delimiters: [
          { left: "$$", right: "$$", display: true },
          { left: "$", right: "$", display: false }
        ],
        throwOnError: false
      });
    }
  }

  // Populate Download Buttons
  const downloadContainer = document.getElementById("download-buttons-container");
  if (downloadContainer) {
    downloadContainer.innerHTML = "";

    const files = studyPackage.files || {};
    if (files.pdf) {
      const pdfBtn = document.createElement("a");
      pdfBtn.href = files.pdf;
      pdfBtn.className = "btn-download pdf";
      pdfBtn.setAttribute("download", "");
      pdfBtn.innerHTML = `<span>📕</span> PDF Guide`;
      downloadContainer.appendChild(pdfBtn);
    }
    if (files.pptx) {
      const pptxBtn = document.createElement("a");
      pptxBtn.href = files.pptx;
      pptxBtn.className = "btn-download pptx";
      pptxBtn.setAttribute("download", "");
      pptxBtn.innerHTML = `<span>📊</span> PPTX Slides`;
      downloadContainer.appendChild(pptxBtn);
    }
    if (files.docx) {
      const docxBtn = document.createElement("a");
      docxBtn.href = files.docx;
      docxBtn.className = "btn-download docx";
      docxBtn.setAttribute("download", "");
      docxBtn.innerHTML = `<span>📝</span> Word DOCX`;
      downloadContainer.appendChild(docxBtn);
    }
  }

  // Populate Citations List
  const sourcesList = document.getElementById("modal-sources-list");
  if (sourcesList) {
    sourcesList.innerHTML = "";
    const sources = studyPackage.sources || [];
    if (sources.length > 0) {
      sources.forEach((src) => {
        const li = document.createElement("li");
        const a = document.createElement("a");
        a.href = src.link;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.textContent = `📖 ${src.title || src.link}`;
        li.appendChild(a);
        sourcesList.appendChild(li);
      });
    } else {
      const li = document.createElement("li");
      li.textContent = `📖 Authoritative Academic Reference: ${studyPackage.target_book || "Prescribed Textbook"}`;
      sourcesList.appendChild(li);
    }
  }

  modal.classList.remove("hidden");
}
