$(document).ready(function(){
  if(window.navigator.userAgent.toLowerCase().indexOf("firefox")>0){ //firefox innerText define
  HTMLElement.prototype.__defineGetter__( "innerText",
  function(){
  var anyString = "";
  var childS = this.childNodes;
  for(var i=0; i <childS.length; i++) {
  if(childS[i].nodeType==1)
  anyString += childS[i].tagName=="BR" ? '\n' : childS[i].innerText;
  else if(childS[i].nodeType==3)
  anyString += childS[i].nodeValue;
  }
  return anyString;
  }
  );
  HTMLElement.prototype.__defineSetter__( "innerText",
  function(sText){
  this.textContent=sText;
  }
  );
}
   $(".navigation-arrow.left").click(function(){
       $("#navigation").animate({'margin-left':+0+"px"});
       $(".navigation-arrow.left").addClass("in");
       $(".navigation-arrow.right.in ").removeClass("in");

   })
   $(".navigation-arrow.right").click(function(){
       var len=$("#navigation").width();
       var left=len-$(".scroll").width()-1;
       $("#navigation").animate({'margin-left':+-left+"px"});
       $(".navigation-arrow.right").addClass("in");
       $(".navigation-arrow.left.in ").removeClass("in");
   })

    $(".service-select").click(function(){
       $(".service-select").removeClass("clicked");
       $(this).addClass("clicked");
       $(".service-select").find("label").removeClass("clicked");
       $(this).find("label").addClass("clicked");
       $("#abstract-box").slideDown();
       document.getElementById("type").innerText=this.innerText;
    })

    $(".service-select").mouseover(function(){
        $(this).find("label").addClass("hover");
    })

    $(".service-select").mouseout(function(){
        $(".service-select").find("label").removeClass("hover");
    })


   $(".detail-switch").click(function(){
       $("#open-detail").toggle();
       $("#close-detail").toggle();
       $(".service-detail").slideToggle();
   })


});