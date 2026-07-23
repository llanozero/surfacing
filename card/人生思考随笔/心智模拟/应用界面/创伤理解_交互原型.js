(function () {
  const DATA_URL = "./创伤理解_交互数据.json";

  const ui = {
    phaseBadge: document.getElementById("phaseBadge"),
    stepMeta: document.getElementById("stepMeta"),
    progressBar: document.getElementById("progressBar"),
    contentArea: document.getElementById("contentArea"),
    actionArea: document.getElementById("actionArea"),
    historyList: document.getElementById("historyList"),
    stateSummary: document.getElementById("stateSummary"),
    restartBtn: document.getElementById("restartBtn"),
    themeSelect: document.getElementById("themeSelect"),
    cardSelect: document.getElementById("cardSelect"),
    prevBtn: document.getElementById("prevBtn"),
    nextBtn: document.getElementById("nextBtn"),
    exportBtn: document.getElementById("exportBtn")
  };

  const store = {
    theme: "dark",
    stage: "loading",
    cardIndex: -1,
    classifierIndex: -1,
    preflightIndex: -1,
    answers: {
      reading_preference: null,
      attention_bandwidth: null,
      life_stage: null,
      attitude: null,
      entryMode: null,
      supportRole: null,
      pace: null
    },
    state: {},
    history: [],
    data: null,
    loadError: null,
    displayMode: null,
    cardViewMode: "default",
    classifierViewMode: "default"
  };

  function applyTheme(theme) {
    store.theme = theme;
    document.body.setAttribute("data-theme", theme);
    ui.themeSelect.value = theme;
    try {
      localStorage.setItem("trauma-prototype-theme", theme);
    } catch (error) {}
  }

  function pushHistory(title, value) {
    store.history.unshift({ title, value });
    if (store.history.length > 12) {
      store.history.length = 12;
    }
  }

  function applyEffects(effects = {}) {
    Object.entries(effects).forEach(([key, value]) => {
      if (typeof store.state[key] !== "number") {
        store.state[key] = 0;
      }
      store.state[key] += value;
    });
  }

  function progressValue() {
    if (!store.data) return 0;
    if (store.stage === "entry") return 0;
    if (store.stage === "preflight") return 10 + ((store.preflightIndex + 1) / store.data.preflight.length) * 20;
    if (store.stage === "modeChoice") return 35;
    if (store.stage === "article") return 55;
    if (store.stage === "cards") return ((store.cardIndex + 1) / store.data.cards.length) * 70;
    if (store.stage === "classifier") return 70 + ((store.classifierIndex + 1) / store.data.classifier.length) * 25;
    if (store.stage === "result" || store.stage === "paused") return 100;
    return 8;
  }

  function renderStateSummary() {
    const {
      comprehensionDepth = 0,
      emotionalOpenness = 0,
      structuralCuriosity = 0,
      defensiveness = 0,
      pacingTolerance = 0
    } = store.state;
    ui.stateSummary.innerHTML = `
      <div>理解深度：<strong>${comprehensionDepth}</strong></div>
      <div>情绪开放：<strong>${emotionalOpenness}</strong></div>
      <div>结构好奇：<strong>${structuralCuriosity}</strong></div>
      <div>防御反应：<strong>${defensiveness}</strong></div>
      <div>节奏耐受：<strong>${pacingTolerance}</strong></div>
      <hr>
      <div>展示模式：<strong>${store.displayMode || "未判定"}</strong></div>
      <div>阅读偏好：<strong>${store.answers.reading_preference || "未判定"}</strong></div>
      <div>当前带宽：<strong>${store.answers.attention_bandwidth || "未判定"}</strong></div>
      <div>阶段侧写：<strong>${store.answers.life_stage || "未判定"}</strong></div>
      <hr>
      <div>态度：<strong>${store.answers.attitude || "未判定"}</strong></div>
      <div>入口：<strong>${store.answers.entryMode || "未判定"}</strong></div>
      <div>角色：<strong>${store.answers.supportRole || "未判定"}</strong></div>
      <div>节奏：<strong>${store.answers.pace || "未判定"}</strong></div>
    `;
  }

  function populateCardSelect() {
    if (!store.data) return;
    const existing = Array.from(ui.cardSelect.querySelectorAll("option")).slice(1);
    existing.forEach((option) => option.remove());
    store.data.cards.forEach((card, index) => {
      const option = document.createElement("option");
      option.value = String(index);
      option.textContent = `${index + 1}. ${card.title}`;
      ui.cardSelect.appendChild(option);
    });
  }

  function renderHistory() {
    ui.historyList.innerHTML = store.history.length
      ? store.history.map((item) => `<div class="history-item"><strong>${item.title}</strong><br>${item.value}</div>`).join("")
      : `<div class="history-item tiny">还没有操作历史。</div>`;
  }

  function updateTopNav() {
    const inCards = store.stage === "cards";
    const inClassifier = store.stage === "classifier";
    const inPreflight = store.stage === "preflight";
    const hasData = Boolean(store.data);

    ui.cardSelect.disabled = !hasData;
    ui.prevBtn.disabled = !(inPreflight || inCards || inClassifier || store.stage === "article" || store.stage === "result" || store.stage === "paused");
    ui.nextBtn.disabled = !inCards;
    ui.exportBtn.disabled = !(store.stage === "result" || inClassifier || store.history.length);

    if (inCards) {
      ui.cardSelect.value = String(store.cardIndex);
      ui.prevBtn.disabled = store.cardIndex <= 0;
      ui.nextBtn.disabled = store.cardIndex >= store.data.cards.length - 1;
    } else {
      ui.cardSelect.value = "";
    }
  }

  function makeButton(label, onClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", onClick);
    ui.actionArea.appendChild(button);
  }

  function renderOptionCards(options, onSelect) {
    ui.actionArea.innerHTML = "";
    options.forEach((option) => {
      const stack = document.createElement("div");
      stack.className = "option-stack";

      const button = document.createElement("button");
      button.type = "button";
      button.textContent = option.label;
      button.addEventListener("click", () => onSelect(option));
      stack.appendChild(button);

      const detail = document.createElement("div");
      detail.className = "option-detail-card";
      const parts = [];
      if (option.hint) {
        parts.push(`<div class="tiny">${escapeHtml(option.hint)}</div>`);
      }
      if (option.scene) {
        parts.push(`<p class="tiny"><strong>情境</strong>${escapeHtml(option.scene)}</p>`);
      }
      if (option.example) {
        parts.push(`<p class="tiny"><strong>例子</strong>${escapeHtml(option.example)}</p>`);
      }
      if (option.story) {
        parts.push(`<p class="tiny"><strong>画面</strong>${escapeHtml(option.story)}</p>`);
      }
      detail.innerHTML = parts.join("");
      stack.appendChild(detail);
      ui.actionArea.appendChild(stack);
    });
  }

  function renderLoading() {
    ui.phaseBadge.textContent = "载入中";
    ui.stepMeta.textContent = "正在读取交互数据";
    ui.contentArea.innerHTML = `
      <div class="eyebrow">Loading</div>
      <h2>正在准备原型</h2>
      <p class="content">页面正在读取外部数据文件，请稍等。</p>
    `;
    ui.actionArea.innerHTML = "";
    updateTopNav();
  }

  function renderLoadError() {
    ui.phaseBadge.textContent = "数据未载入";
    ui.stepMeta.textContent = "外部 JSON 读取失败";
    ui.contentArea.innerHTML = `
      <div class="eyebrow">Load Error</div>
      <h2>没有读到外部数据文件</h2>
      <div class="result warn">
        <p class="content">当前页面会优先读取同目录下的 <code>创伤理解_交互数据.json</code>。如果你是直接双击打开 <code>html</code>，浏览器可能会拦截本地文件之间的读取。</p>
        <p class="tiny">更稳的方式是把这个目录放到本地静态服务里打开，或者改用支持本地文件读取策略较宽松的环境。</p>
      </div>
      <div class="card">
        <p class="tiny">错误信息：${escapeHtml(store.loadError || "unknown error")}</p>
      </div>
    `;
    ui.actionArea.innerHTML = "";
    makeButton("重试读取", loadDataAndStart);
    updateTopNav();
  }

  function renderEntry() {
    ui.phaseBadge.textContent = "入口";
    ui.stepMeta.textContent = "准备开始";
    ui.contentArea.innerHTML = `
      <div class="eyebrow">Start</div>
      <h2>${store.data.entry.title}</h2>
      <p class="content">${store.data.entry.prompt}</p>
    `;
    ui.actionArea.innerHTML = "";
    makeButton("开始侧写", () => {
      store.stage = "preflight";
      store.preflightIndex = 0;
      render();
    });
    updateTopNav();
  }

  function inferDisplayMode() {
    const mapping = store.data.modeMapping || {};
    const signals = [
      store.answers.reading_preference,
      store.answers.attention_bandwidth,
      store.answers.life_stage
    ].map((key) => mapping[key]).filter(Boolean);
    const flowScore = signals.filter((item) => item === "flow").length;
    const longformScore = signals.filter((item) => item === "longform").length;
    return longformScore > flowScore ? "longform" : "flow";
  }

  function renderPreflight() {
    const question = store.data.preflight[store.preflightIndex];
    ui.phaseBadge.textContent = `展示判断 ${store.preflightIndex + 1}/${store.data.preflight.length}`;
    ui.stepMeta.textContent = question.title;
    ui.contentArea.innerHTML = `
      <div class="eyebrow">Preflight</div>
      <h2>${question.title}</h2>
      <p class="content">${question.prompt}</p>
    `;
    renderOptionCards(question.options, (option) => {
        pushHistory(question.title, option.label);
        store.answers[question.id] = option.id;
        if (store.preflightIndex === store.data.preflight.length - 1) {
          store.displayMode = inferDisplayMode();
          store.stage = "modeChoice";
          render();
          return;
        }
        store.preflightIndex += 1;
        render();
    });
    updateTopNav();
  }

  function renderModeChoice() {
    const recommended = store.displayMode || "flow";
    const recommendedMeta = store.data.modes[recommended];
    const alternate = recommended === "flow" ? "longform" : "flow";
    const alternateMeta = store.data.modes[alternate];
    ui.phaseBadge.textContent = "展示推荐";
    ui.stepMeta.textContent = recommendedMeta.title;
    ui.contentArea.innerHTML = `
      <div class="eyebrow">Mode Match</div>
      <h2>更适合你的展示方式</h2>
      <div class="result">
        <div>
          <div class="badge">推荐</div>
          <p class="content">${recommendedMeta.title}</p>
          <p class="subtle">${recommendedMeta.description}</p>
        </div>
      </div>
      <div class="card">
        <p class="tiny">这是根据阅读偏好、当前带宽和人生阶段侧写做的推荐，不是强制分配。你仍然可以手动改走另一条。</p>
      </div>
    `;
    ui.actionArea.innerHTML = "";
    makeButton(`按推荐进入：${recommendedMeta.title}`, () => {
      if (recommended === "flow") {
        store.stage = "cards";
        store.cardIndex = 0;
      } else {
        store.stage = "article";
      }
      render();
    });
    makeButton(`改走：${alternateMeta.title}`, () => {
      store.displayMode = alternate;
      if (alternate === "flow") {
        store.stage = "cards";
        store.cardIndex = 0;
      } else {
        store.stage = "article";
      }
      render();
    });
    updateTopNav();
  }

  function renderArticle() {
    const article = store.data.fullArticle;
    ui.phaseBadge.textContent = "结构化原文";
    ui.stepMeta.textContent = article.title;
    const sections = article.sections
      .map((section) => `<div class="card"><h3>${section.title}</h3><p class="content">${section.text}</p></div>`)
      .join("");
    ui.contentArea.innerHTML = `
      <div class="eyebrow">Longform</div>
      <h2>${article.title}</h2>
      <p class="subtle">${article.intro}</p>
      ${sections}
    `;
    ui.actionArea.innerHTML = "";
    makeButton("进入分类器", () => {
      store.stage = "classifier";
      store.classifierIndex = 0;
      pushHistory("展示方式", "结构化原文");
      render();
    });
    makeButton("改看单卡版", () => {
      store.displayMode = "flow";
      store.stage = "cards";
      store.cardIndex = 0;
      render();
    });
    updateTopNav();
  }

  function renderCard() {
    const card = store.data.cards[store.cardIndex];
    const viewMode = store.cardViewMode || "default";
    let bodyTitle = card.title;
    let bodyText = card.text;
    if (viewMode === "story" && card.storyView) {
      bodyTitle = card.storyView.title;
      bodyText = card.storyView.text;
    }
    if (viewMode === "analysis" && card.analysisView) {
      bodyTitle = card.analysisView.title;
      bodyText = card.analysisView.text;
    }
    ui.phaseBadge.textContent = `阅读卡片 ${store.cardIndex + 1}/${store.data.cards.length}`;
    ui.stepMeta.textContent = card.description;
    ui.contentArea.innerHTML = `
      <div class="eyebrow">Single Card</div>
      <h2>${card.title}</h2>
      <p class="subtle">${card.description}</p>
      <div class="view-switches">
        <button type="button" data-view-mode="default">原卡正文</button>
        <button type="button" data-view-mode="analysis">结构化解说版</button>
        <button type="button" data-view-mode="story">短篇剧情版</button>
      </div>
      <div class="card">
        <h3>${bodyTitle}</h3>
        <p class="content">${bodyText}</p>
      </div>
    `;
    Array.from(ui.contentArea.querySelectorAll("[data-view-mode]")).forEach((button) => {
      if (button.getAttribute("data-view-mode") === viewMode) {
        button.style.borderColor = "var(--accent)";
        button.style.background = "color-mix(in srgb, var(--panel) 80%, var(--accent-soft))";
      }
      button.addEventListener("click", () => {
        store.cardViewMode = button.getAttribute("data-view-mode");
        render();
      });
    });
    renderOptionCards(card.responses, (response) => {
        pushHistory(card.title, response.label);
        applyEffects(response.effects);
        if (response.pause) {
          store.stage = "paused";
          render();
          return;
        }
        if (response.next === "classifier") {
          store.stage = "classifier";
          store.classifierIndex = 0;
          render();
          return;
        }
        store.cardIndex += 1;
        store.cardViewMode = "default";
        render();
    });
    updateTopNav();
  }

  function renderClassifier() {
    const question = store.data.classifier[store.classifierIndex];
    const viewMode = store.classifierViewMode || "default";
    let bodyTitle = question.title;
    let bodyText = question.prompt;
    if (viewMode === "story" && question.storyView) {
      bodyTitle = question.storyView.title;
      bodyText = question.storyView.text;
    }
    if (viewMode === "analysis" && question.analysisView) {
      bodyTitle = question.analysisView.title;
      bodyText = question.analysisView.text;
    }
    ui.phaseBadge.textContent = `分类器 ${store.classifierIndex + 1}/${store.data.classifier.length}`;
    ui.stepMeta.textContent = question.title;
    ui.contentArea.innerHTML = `
      <div class="eyebrow">Classifier</div>
      <h2>${question.title}</h2>
      <div class="view-switches">
        <button type="button" data-classifier-view="default">原问题</button>
        <button type="button" data-classifier-view="analysis">结构化解说版</button>
        <button type="button" data-classifier-view="story">短篇剧情版</button>
      </div>
      <div class="card">
        <h3>${bodyTitle}</h3>
        <p class="content">${bodyText}</p>
      </div>
    `;
    Array.from(ui.contentArea.querySelectorAll("[data-classifier-view]")).forEach((button) => {
      if (button.getAttribute("data-classifier-view") === viewMode) {
        button.style.borderColor = "var(--accent)";
        button.style.background = "color-mix(in srgb, var(--panel) 80%, var(--accent-soft))";
      }
      button.addEventListener("click", () => {
        store.classifierViewMode = button.getAttribute("data-classifier-view");
        render();
      });
    });
    renderOptionCards(question.options, (option) => {
        pushHistory(question.title, option.label);
        store.answers[question.id] = option.id;
        if (store.classifierIndex === store.data.classifier.length - 1) {
          store.stage = "result";
          store.classifierViewMode = "default";
          render();
          return;
        }
        store.classifierIndex += 1;
        store.classifierViewMode = "default";
        render();
    });
    updateTopNav();
  }

  function resolveInterface() {
    const { attitude, entryMode, supportRole, pace } = store.answers;
    if (pace === "pause") {
      return store.data.interfaces.pause;
    }
    if (attitude === "defensive") {
      return store.data.interfaces["defensive|*|*"];
    }
    const exactKey = `${attitude}|${entryMode}|${supportRole}`;
    return store.data.interfaces[exactKey] || store.data.interfaces.default;
  }

  function renderResult() {
    const result = resolveInterface();
    ui.phaseBadge.textContent = "接口输出";
    ui.stepMeta.textContent = result.title;
    ui.contentArea.innerHTML = `
      <div class="eyebrow">Matched Interface</div>
      <h2>${result.title}</h2>
      <div class="result">
        <div>
          <div class="badge">推荐承接句</div>
          <p class="content">${result.recommended}</p>
        </div>
        <div class="result warn">
          <div class="badge" style="background:#f0d9bc;color:#7b4e17;">当前避免</div>
          <p class="content">${result.avoid}</p>
        </div>
      </div>
    `;
    ui.actionArea.innerHTML = "";
    makeButton("重新跑一遍", resetFlow);
    makeButton("回到分类器最后一题", () => {
      store.stage = "classifier";
      store.classifierIndex = store.data.classifier.length - 1;
      render();
    });
    updateTopNav();
  }

  function renderPause() {
    ui.phaseBadge.textContent = "柔性暂停";
    ui.stepMeta.textContent = "先停在这里也没问题";
    ui.contentArea.innerHTML = `
      <div class="eyebrow">Pause</div>
      <h2>我们先停在这里</h2>
      <div class="result warn">
        <p class="content">我们可以先停在这里，不急着把后面的内容走完。</p>
        <p class="tiny">暂停不是拒绝，也不需要立刻补充更多解释。</p>
      </div>
    `;
    ui.actionArea.innerHTML = "";
    makeButton("从头再来", resetFlow);
    makeButton("继续当前流程", () => {
      if (store.cardIndex < 0) {
        store.stage = "entry";
      } else if (store.cardIndex < store.data.cards.length - 1) {
        store.stage = "cards";
      } else {
        store.stage = "classifier";
        if (store.classifierIndex < 0) {
          store.classifierIndex = 0;
        }
      }
      render();
    });
    updateTopNav();
  }

  function render() {
    ui.progressBar.style.width = `${progressValue()}%`;
    renderStateSummary();
    renderHistory();
    if (store.stage === "loading") {
      renderLoading();
      return;
    }
    if (store.stage === "loadError") {
      renderLoadError();
      return;
    }
    if (store.stage === "entry") {
      renderEntry();
      return;
    }
    if (store.stage === "preflight") {
      renderPreflight();
      return;
    }
    if (store.stage === "modeChoice") {
      renderModeChoice();
      return;
    }
    if (store.stage === "article") {
      renderArticle();
      return;
    }
    if (store.stage === "cards") {
      renderCard();
      return;
    }
    if (store.stage === "classifier") {
      renderClassifier();
      return;
    }
    if (store.stage === "result") {
      renderResult();
      return;
    }
    if (store.stage === "paused") {
      renderPause();
    }
  }

  function resetFlow() {
    store.stage = "entry";
    store.cardIndex = -1;
    store.classifierIndex = -1;
    store.preflightIndex = -1;
    store.answers = {
      reading_preference: null,
      attention_bandwidth: null,
      life_stage: null,
      attitude: null,
      entryMode: null,
      supportRole: null,
      pace: null
    };
    store.state = { ...(store.data ? store.data.initialState : {}) };
    store.history = [];
    store.displayMode = null;
    store.cardViewMode = "default";
    store.classifierViewMode = "default";
    render();
  }

  function goToPrevious() {
    if (store.stage === "preflight" && store.preflightIndex > 0) {
      store.preflightIndex -= 1;
      render();
      return;
    }
    if (store.stage === "cards" && store.cardIndex > 0) {
      store.cardIndex -= 1;
      store.cardViewMode = "default";
      render();
      return;
    }
    if (store.stage === "classifier" && store.classifierIndex > 0) {
      store.classifierIndex -= 1;
      store.classifierViewMode = "default";
      render();
      return;
    }
    if (store.stage === "result") {
      store.stage = "classifier";
      store.classifierIndex = store.data.classifier.length - 1;
      store.classifierViewMode = "default";
      render();
      return;
    }
    if (store.stage === "paused") {
      store.stage = "cards";
      render();
      return;
    }
    if (store.stage === "article") {
      store.stage = "modeChoice";
      render();
    }
  }

  function goToNext() {
    if (store.stage === "cards" && store.cardIndex < store.data.cards.length - 1) {
      store.cardIndex += 1;
      store.cardViewMode = "default";
      render();
    }
  }

  function exportSnapshot() {
    const payload = {
      exportedAt: new Date().toISOString(),
      stage: store.stage,
      currentCardIndex: store.cardIndex,
      currentClassifierIndex: store.classifierIndex,
      currentPreflightIndex: store.preflightIndex,
      displayMode: store.displayMode,
      answers: store.answers,
      state: store.state,
      history: store.history,
      resolvedInterface: store.stage === "result" ? resolveInterface() : null
    };
    const text = JSON.stringify(payload, null, 2);
    const blob = new Blob([text], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "创伤理解_分类结果.json";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  async function loadDataAndStart() {
    store.stage = "loading";
    store.loadError = null;
    render();
    try {
      const response = await fetch(DATA_URL, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const json = await response.json();
      store.data = json;
      store.state = { ...json.initialState };
      populateCardSelect();
      resetFlow();
    } catch (error) {
      store.loadError = error && error.message ? error.message : String(error);
      store.stage = "loadError";
      render();
    }
  }

  function escapeHtml(text) {
    return String(text)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  ui.restartBtn.addEventListener("click", resetFlow);
  ui.prevBtn.addEventListener("click", goToPrevious);
  ui.nextBtn.addEventListener("click", goToNext);
  ui.exportBtn.addEventListener("click", exportSnapshot);
  ui.cardSelect.addEventListener("change", (event) => {
    if (!store.data || event.target.value === "") return;
    store.stage = "cards";
    store.cardIndex = Number(event.target.value);
    store.cardViewMode = "default";
    render();
  });
  ui.themeSelect.addEventListener("change", (event) => {
    applyTheme(event.target.value);
  });

  try {
    const savedTheme = localStorage.getItem("trauma-prototype-theme");
    applyTheme(savedTheme || "dark");
  } catch (error) {
    applyTheme("dark");
  }

  render();
  loadDataAndStart();
})();
