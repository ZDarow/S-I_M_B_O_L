menu.onclick = function myFunction() {
  var x = document.getElementById("funkVerhNav");
  if (x.className === "menu_odin") {
    x.className += "  responsive";
  } else {
    x.className = "menu_odin";
  }
    var x = document.getElementById("mask"); // для затемнения контента
  if (x.className === "main") {
    x.className += "  responsive";
  } else {
    x.className = "main";
  }
}

menu2.onclick = function myFunction() {
  var x = document.getElementById("pravMenuDin");
  if (x.className === "menu_dva") {
    x.className += "  responsive";
  } else {
    x.className = "menu_dva";
  }
  var x = document.getElementById("mask2"); // для затемнения контента
  if (x.className === "mute") {
    x.className += "  responsive";
  } else {
    x.className = "mute";
  }
}

menu3.onclick = function myFunction() {
  var x = document.getElementById("myPoisk");
  if (x.className === "poisk") {
    x.className += "  responsive";
  } else {
    x.className = "poisk";
  }
}

  // замена лупы на close
 var x=false
  function imgchange(obj,imgX,imgY) {
   if  (x){
   obj.src=imgX
   } else {
   obj.src=imgY
   }
  x=!x
 }
 
 // ВК асинхрон
(function(a, c, f) { function g() { var d, a = c.getElementsByTagName(f)[0], b = function(b, e) { c.getElementById(e) || (d = c.createElement(f), d.src = b, d.async = !0, e && (d.id = e), a.parentNode.insertBefore(d, a)) };
 b("//vk.com/js/api/openapi.js");
 }
a.addEventListener ? a.addEventListener("load", g, !1) : a.attachEvent && a.attachEvent("onload", g)
})(window, document, "script");
 
 window.vkAsyncInit = function () { 
VK.init({apiId: 5224212, onlyWidgets: true});
	
VK.Widgets.Like("vk_like", {type: "button", verb: 0, height: 20, pageUrl: "https://reno-symbol.ru", pageTitle: "Руководство  по ремонту Renault Symbol", pageDescription: "Руководство по ремонту и эксплуатации Renault Symbol / Рено Симбол", pageImage:"https://reno-symbol.ru/img/ind.png"});
  	};
	
 // предзагрузка
  var img1=new Image(); 
img1.src='img/psk_icon.png'; 