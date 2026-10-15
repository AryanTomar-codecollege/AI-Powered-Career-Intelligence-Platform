(() => {
  const cfg = window.CAREERCAST_CONFIG;
  const $ = (id) => document.getElementById(id);
  const required = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "API_BASE_URL"];
  if (!cfg || required.some((key) => !cfg[key] || cfg[key].includes("YOUR_"))) {
    window.addEventListener("DOMContentLoaded", () => {
      $("authMessage").textContent = "Setup needed: copy config.js.example to config.js and add your Supabase project URL and public anon/publishable key.";
    });
    return;
  }
  const supabase = window.supabase.createClient(cfg.SUPABASE_URL, cfg.SUPABASE_ANON_KEY);
  let mode = "signin";
  let profile = null;

  function message(id, text, success = false) {
    const el = $(id); el.textContent = text; el.classList.toggle("success", success);
  }
  function listFromLines(value) { return value.split(/\r?\n/).map(x => x.trim()).filter(Boolean); }
  function listFromCsv(value) { return value.split(",").map(x => x.trim()).filter(Boolean); }
  function showAuth() {
    $("authPanel").classList.remove("hidden"); $("workspace").classList.add("hidden");
    $("logoutBtn").classList.add("hidden");
  }
  function showWorkspace() {
    $("authPanel").classList.add("hidden"); $("workspace").classList.remove("hidden");
    $("logoutBtn").classList.remove("hidden");
  }
  function setMode(next) {
    mode = next;
    $("signinTab").classList.toggle("selected", mode === "signin");
    $("signupTab").classList.toggle("selected", mode === "signup");
    $("nameWrap").classList.toggle("hidden", mode !== "signup");
    $("authTitle").textContent = mode === "signin" ? "Welcome back" : "Create your account";
    $("authSubtitle").textContent = mode === "signin" ? "Sign in to continue to your workspace." : "Start building your career profile.";
    $("authSubmit").textContent = mode === "signin" ? "Sign in" : "Create account";
    $("password").autocomplete = mode === "signin" ? "current-password" : "new-password";
    message("authMessage", "");
  }
  async function api(path, options = {}) {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.access_token) throw new Error("Your session has expired. Please sign in again.");
    const headers = new Headers(options.headers || {});
    headers.set("Authorization", `Bearer ${session.access_token}`);
    if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
    const response = await fetch(`${cfg.API_BASE_URL.replace(/\/$/, "")}${path}`, {...options, headers});
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status}).`);
    return payload;
  }
  function lines(value) { return value.join("\n"); }
  async function loadProfile() {
    profile = await api("/api/profile");
    $("profileName").value = profile.full_name || "";
    $("headline").value = profile.headline || "";
    $("location").value = profile.location || "";
    $("education").value = Array.isArray(profile.education) ? lines(profile.education.map(x => typeof x === "string" ? x : JSON.stringify(x))) : "";
    $("skills").value = (profile.skills || []).join(", ");
    $("certifications").value = lines(profile.certifications || []);
    $("experience").value = Array.isArray(profile.work_experience) ? lines(profile.work_experience.map(x => typeof x === "string" ? x : JSON.stringify(x))) : "";
    const name = profile.full_name || profile.email.split("@")[0];
    $("welcomeName").textContent = name;
    $("avatar").textContent = name.charAt(0).toUpperCase();
  }
  async function loadResumes() {
    const resumes = await api("/api/resumes");
    const host = $("resumeList"); host.replaceChildren();
    if (!resumes.length) { host.textContent = "No resumes uploaded yet."; host.className = "resume-list muted"; return; }
    host.className = "resume-list";
    resumes.forEach(resume => {
      const item = document.createElement("div"); item.className = "resume-item";
      const title = document.createElement("b"); title.textContent = resume.filename;
      const meta = document.createElement("small"); meta.textContent = `${resume.skills.length} skill keywords · ${new Date(resume.created_at).toLocaleDateString()}`;
      item.append(title, meta); host.append(item);
    });
  }
  async function enterWorkspace() {
    showWorkspace();
    try { await loadProfile(); await loadResumes(); }
    catch (error) { message("profileMessage", error.message); }
  }
  $("signinTab").addEventListener("click", () => setMode("signin"));
  $("signupTab").addEventListener("click", () => setMode("signup"));
  $("authForm").addEventListener("submit", async (event) => {
    event.preventDefault(); $("authSubmit").disabled = true; message("authMessage", "Please wait…");
    try {
      const email = $("email").value.trim(); const password = $("password").value;
      if (mode === "signin") {
        const { error } = await supabase.auth.signInWithPassword({email, password});
        if (error) throw error;
        await enterWorkspace();
      } else {
        const { data, error } = await supabase.auth.signUp({
          email, password, options: { data: { full_name: $("fullName").value.trim() } }
        });
        if (error) throw error;
        if (data.session) await enterWorkspace();
        else message("authMessage", "Account created. Check your email to confirm it, then sign in.", true);
      }
    } catch (error) { message("authMessage", error.message || "Authentication failed."); }
    finally { $("authSubmit").disabled = false; }
  });
  $("logoutBtn").addEventListener("click", async () => {
    const { error } = await supabase.auth.signOut();
    if (error) message("profileMessage", error.message);
    showAuth();
  });
  $("profileForm").addEventListener("submit", async (event) => {
    event.preventDefault(); message("profileMessage", "Saving…");
    try {
      await api("/api/profile", {method:"PUT", body:JSON.stringify({
        full_name:$("profileName").value.trim() || null,
        headline:$("headline").value.trim() || null,
        location:$("location").value.trim() || null,
        education:listFromLines($("education").value),
        skills:listFromCsv($("skills").value),
        certifications:listFromLines($("certifications").value),
        work_experience:listFromLines($("experience").value)
      })});
      await loadProfile(); message("profileMessage", "Profile saved successfully.", true);
    } catch (error) { message("profileMessage", error.message); }
  });
  $("resumeForm").addEventListener("submit", async (event) => {
    event.preventDefault(); const file = $("resumeFile").files[0];
    if (!file) return;
    const button = $("resumeForm").querySelector("button[type=submit]");
    button.disabled = true; message("resumeMessage", "Uploading and parsing…");
    try {
      const form = new FormData(); form.append("file", file);
      const result = await api("/api/resumes/parse", {method:"POST", body:form});
      message("resumeMessage", "Resume parsed successfully. Extracted skills were added to your profile.", true);
      const host = $("parseResult"); host.classList.remove("hidden"); host.replaceChildren();
      const addSection = (title, values) => {
        const h = document.createElement("h3"); h.textContent = title;
        const chips = document.createElement("div"); chips.className = "chips";
        (values.length ? values : ["No matches detected"]).forEach(value => {
          const chip = document.createElement("span"); chip.className = "chip"; chip.textContent = value; chips.append(chip);
        });
        host.append(h, chips);
      };
      addSection("Skill keywords", result.skills);
      addSection("Likely job titles", result.job_titles);
      addSection("Education / institution signals", result.institutions);
      addSection("Date ranges", result.duration_markers);
      await loadProfile(); await loadResumes(); $("resumeFile").value = "";
    } catch (error) { message("resumeMessage", error.message); }
    finally { button.disabled = false; }
  });
  $("refreshResumes").addEventListener("click", async () => {
    try { await loadResumes(); } catch (error) { message("profileMessage", error.message); }
  });
  supabase.auth.onAuthStateChange((_event, session) => {
    if (session) enterWorkspace(); else showAuth();
  });
  (async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (session) await enterWorkspace(); else showAuth();
  })();
})();