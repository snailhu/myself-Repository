		function popupDiv(item,name) {
			var flag=item;
			$("#"+name).empty();
			var currentDate= new Date();
			$("#"+name).append("<table cellspacing='1'><tr><td class='th1'><button onclick=changeYear('down','"+flag+"')>&lt;&lt;</button></td><td id='year"+flag+"' class='th2'></td><td  class='th3'><button onclick=changeYear('up','"+flag+"')>&gt;&gt;</button></td></tr><tr><td><button onclick=hideDiv('"+item+"','"+name+"',1,'"+flag+"')>1</button></td><td><button onclick=hideDiv('"+item+"','"+name+"',2,'"+flag+"')>2</button></td><td><button onclick=hideDiv('"+item+"','"+name+"',3,'"+flag+"')>3</button></td></tr><tr><td><button onclick=hideDiv('"+item+"','"+name+"',4,'"+flag+"')>4</button></td><td><button onclick=hideDiv('"+item+"','"+name+"',5,'"+flag+"')>5</button></td><td><button onclick=hideDiv('"+item+"','"+name+"',6,'"+flag+"')>6</button></td></tr><tr><td><button onclick=hideDiv('"+item+"','"+name+"',7,'"+flag+"')>7</button></td><td><button onclick=hideDiv('"+item+"','"+name+"',8,'"+flag+"')>8</button></td><td><button onclick=hideDiv('"+item+"','"+name+"',9,'"+flag+"')>9</button></td></tr><tr><td><button onclick=hideDiv('"+item+"','"+name+"',10,'"+flag+"')>10</button></td><td><button onclick=hideDiv('"+item+"','"+name+"',11,'"+flag+"')>11</button></td><td><button onclick=hideDiv('"+item+"','"+name+"',12,'"+flag+"')>12</button></td></tr></table>");
			$("#year"+flag).append(currentDate.getFullYear());
			$("#"+name).show();
		} 
		function hideDiv(tag,name,item,flag) { 
			var time=$("#year"+flag).text();
			switch(item){
				case 1:
					time+="-01";
					break;
				case 2:
					time+="-02";
					break;
				case 3:
					time+="-03"
					break;
				case 4:
					time+="-04"
					break;
				case 5:
					time+="-05"
					break;
				case 6:
					time+="-06"
					break;
				case 7:
					time+="-07"
					break;
				case 8:
				time+="-08"
					break;
				case 9:
				time+="-09"
					break;
				case 10:
				time+="-10"
					break;
				case 11:
				time+="-11"
					break;
				case 12:
				time+="-12"
					break;
			}
			$("#"+tag).attr("value",time);
			$("#"+name).animate({opacity: "hide" }, "slow"); 
			$("#"+name).empty();
		}
		
		var currentDate= new Date();
		var temp= currentDate.getFullYear();
		function changeYear(item,flag){
			if(item=="up"){
				$("#year"+flag).empty();
				$("#year"+flag).append(++temp);
			}
			else{
				$("#year"+flag).empty();
				var currentDate= new Date();
				$("#year"+flag).append(--temp);
			}
		}
		function showTime(item,name){
			popupDiv(item.id,name);
		}