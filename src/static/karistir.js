function degistir(){
	document.getElementById("vkey").innerHTML = "";
	var myArray = ['0','1','2','3','4','5','6','7','8','9'];
	var mustafaninArray = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','r','s','t','u','v','y','z','q','w','x'];
	var ozelKarakter = ['!','^','%','&','/','(',')','[',']','?'];
	var newArray2 = shuffle(ozelKarakter);
	var newArray = shuffle(myArray);
	var mustafaninArray2 = shuffle(mustafaninArray);
	for(var i = 0 ; i < ozelKarakter.length ; i++){
		var a = document.createElement("a");
		a.setAttribute("href","javascript:void(0)");
		a.setAttribute("onclick","vkey_add(this)");
		a.setAttribute("class","vkey_key");
		var b = document.createTextNode(newArray2[i]);
		a.appendChild(b);
		document.getElementById("vkey").appendChild(a);
	}
	for(var i = 0 ; i < myArray.length ; i++){
		if(i == 0){
			var c = document.createElement("br");
			document.getElementById("vkey").appendChild(c);
		}
		var a = document.createElement("a");
		a.setAttribute("href","javascript:void(0)");
		a.setAttribute("onclick","vkey_add(this)");
		a.setAttribute("class","vkey_key");
		var b = document.createTextNode(newArray[i]);
		a.appendChild(b);
		document.getElementById("vkey").appendChild(a);
	}
	for(var i = 0 ; i < mustafaninArray.length ; i++){
		if(i % 10 == 0){
			var c = document.createElement("br");
			document.getElementById("vkey").appendChild(c);
		}
		var a = document.createElement("a");
		a.setAttribute("href","javascript:void(0)");
		a.setAttribute("onclick","vkey_add(this)");
		a.setAttribute("class","vkey_key");
		var b = document.createTextNode(mustafaninArray2[i]);
		a.appendChild(b);
		document.getElementById("vkey").appendChild(a);
	}
	
	var c = document.createElement("br");
	document.getElementById("vkey").appendChild(c);
	
	var a = document.createElement("a");
	a.setAttribute("href","javascript:void(0)");
	a.setAttribute("onclick","vkey_cls()");
	a.setAttribute("class","vkey_key");
	var b = document.createTextNode("CLEAR");
	a.appendChild(b);
	document.getElementById("vkey").appendChild(a);
	
	var a = document.createElement("a");
	a.setAttribute("href","javascript:void(0)");
	a.setAttribute("onclick","vkey_cap()");
	a.setAttribute("class","vkey_key");
	var b = document.createTextNode("CAPSLOCK");
	a.appendChild(b);
	document.getElementById("vkey").appendChild(a);
	
	var a = document.createElement("a");
	a.setAttribute("href","javascript:void(0)");
	a.setAttribute("onclick","vkey_bsp()");
	a.setAttribute("class","vkey_key");
	var b = document.createTextNode("BACKSPACE");
	a.appendChild(b);
	document.getElementById("vkey").appendChild(a);
}
function shuffle(o){ //v1.0
    for(var j, x, i = o.length; i; j = parseInt(Math.random() * i), x = o[--i], o[i] = o[j], o[j] = x);
    return o;
};

function ackapa() {
	if(document.getElementById('vkey').style.display == 'none')
		vkey_load();
	else{
		vkey_unload();
		degistir();
	}
}

function disablekeys(){
	return false;
}