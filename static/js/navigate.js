

$(function() {

  // Source:
  // https://css-tricks.com/smooth-scrolling-accessibility/
  $('a[href*="#"]:not([href="#"])').click(function() {
    if (location.pathname.replace(/^\//,'') == this.pathname.replace(/^\//,'') && location.hostname == this.hostname) {
      var target = $(this.hash);
      target = target.length ? target : $('[name=' + this.hash.slice(1) +']');
      if (target.length) {
        $('html, body').animate({
          scrollTop: target.offset().top
        }, 2000);

        target.focus(); // Setting focus
        if (target.is(":focus")){ // Checking if the target was focused
          return false;
        } else {
          target.attr('tabindex','-1'); // Adding tabindex for elements not focusable
          target.focus(); // Setting focus
        };

        return false;
      }
    }
  });

  // $(document).ready(function(){
  //     $('[data-toggle="tooltip"]').tooltip();
  // });

  // Canvas
  var canvas = document.getElementById("canvas");
  // if (canvas.getContext) {
  var ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.lineWidth = 10;
  var lineCap = ['butt', 'round', 'square'];
  ctx.lineCap = lineCap[1];

  function drawLine(xi, yi, cp1x, cp1y, xf, yf) {
    // var canvas = document.getElementById('canvas');
    // if (canvas.getContext) {}
      // var ctx = canvas.getContext('2d');
      // ctx.fillStyle = 'rgb(200, 0, 0)';
      // ctx.fillRect(10, 10, 50, 50); // fillRect(x, y, width, height)
      //
      // ctx.fillStyle = 'rgba(0, 0, 200, 0.5)';
      // ctx.fillRect(30, 30, 50, 50);

      // Draw guides
      ctx.strokeStyle = 'black';
      ctx.beginPath();
      ctx.moveTo(xi, yi);
      ctx.setLineDash([5, 20]); // {lenght:empty space} of line sequence
      ctx.quadraticCurveTo(cp1x, cp1y, xf, yf)

      // ctx.lineTo(140, 10);
      // ctx.moveTo(10, 140);
      // ctx.lineTo(140, 140);
      ctx.stroke();


  }



  var MAX_HEIGHT = 100;
  function render(src, x, y){
  	var image = new Image();
  	image.onload = function(){
  		console.log("image.height: " + image.height);
  		if(image.height > MAX_HEIGHT) {
  			image.width *= MAX_HEIGHT / image.height;
  			image.height = MAX_HEIGHT;
  		}
  		// canvas.width = image.width;
  		// canvas.height = image.height;
  		ctx.drawImage(image, x, y, image.width, image.height);
  	};
  	image.src = src;
  }
  // ctx.font = "25px Arial";
  // ctx.fillText("Select a project", canvas.width / 2 - 70, 120);
  render("www/icons/048-package.svg", canvas.width / 2 - 50, 0);

  render("www/icons/022-money.svg", canvas.width - 100, canvas.height/2 - 30);
  render("www/icons/017-presentation.svg", canvas.width / 2 - 50, canvas.height - 100);
  render("www/icons/027-megaphone.svg", 0, canvas.height/2 - 50);

  // let xi = canvas.width / 2;
  // let yi = 10;
  // let cp1x = 450;
  // let cp1y = 10;
  // let xf = canvas.width - 50;
  // let yf = canvas.height/2 - 50;

  // First line
  drawLine(
    canvas.width / 2 + 70, 70, // xi, yi
    560, 50, // control points
    canvas.width - 50, canvas.height/2 - 37 // end points
  );

  // Second line
  drawLine(
    canvas.width - 50, canvas.height/2 + 75, // xi, yi
    canvas.width - 40, canvas.height - 40, // control points
    canvas.width/2 + 50, canvas.height - 50 // end points
  );

  drawLine(
    canvas.width/2 - 60, canvas.height - 50, // xi, yi
    0 + 40 , canvas.height - 40, // control points
    40, canvas.height/2 + 50 // end points
  );

  drawLine(
    35, canvas.height/2 - 50,
    30, 50,
    canvas.width / 2 - 70,  70,
  )





});
