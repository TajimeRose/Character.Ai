let token = localStorage.getItem("token") || "";
let currentConvId = null;

function saveToken(){
  token = document.getElementById("token").value.trim();
  localStorage.setItem("token", token);
  alert("Saved token (เบต้า)");
}

function h(el, cls, text){
  const d = document.createElement("div");
  d.className = cls; 
  const b = document.createElement("div");
  b.className = "bubble";
  b.textContent = text;
  d.appendChild(b);
  el.appendChild(d);
  el.scrollTop = el.scrollHeight;
}

async function send(){
  const msgEl = document.getElementById("msg");
  const text = msgEl.value.trim();
  const chat = document.getElementById("chat");
  if(!text) return;
  h(chat, "msg user", text);
  msgEl.value = "";

  const character_key = document.getElementById("character").value;

  const res = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type":"application/json",
      ...(token ? {"Authorization":"Bearer "+token} : {})
    },
    body: JSON.stringify({
      character_key,
      text,
      conversation_id: currentConvId
    })
  });
  const j = await res.json();
  if(!res.ok){
    h(chat,"msg ai","[Error] "+(j.error || "unknown"));
    return;
  }
  currentConvId = j.conversation_id;
  h(chat,"msg ai", j.assistant);
}

async function loadList(){
  const list = document.getElementById("list");
  list.innerHTML = "Loading...";
  const res = await fetch("/api/conversations?limit=20", {
    headers: { ...(token ? {"Authorization":"Bearer "+token} : {}) }
  });
  const j = await res.json();
  if(!res.ok){ list.textContent = "Error"; return; }
  list.innerHTML = "";
  j.forEach(item=>{
    const a = document.createElement("a");
    a.href="#";
    a.textContent = (item.title || item._id)+" | "+item.character_key;
    a.style.display = "block";
    a.onclick = async () => {
      const r = await fetch("/api/conversations/"+item._id, {
        headers: { ...(token ? {"Authorization":"Bearer "+token} : {}) }
      });
      const conv = await r.json();
      const chat = document.getElementById("chat");
      chat.innerHTML = "";
      currentConvId = item._id;
      (conv.messages || []).forEach(m=>{
        h(chat, "msg "+(m.role==="user"?"user":"ai"), m.text);
      });
    };
    list.appendChild(a);
  });
}
