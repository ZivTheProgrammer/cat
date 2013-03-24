$(document).ready(function(){
	var detailOn = false;
	$("#searchForm").submit(function(){
		if (!detailOn) {
			$("#resultsDiv").slideDown();
		}
		return false;
	});
	$("#button1").click(function(){
		$("#resultsDiv").slideUp();
		$("#detailView").slideUp();
		detailOn = false;
	});
	$(".course").click(function(){
		$("#resultsDiv").slideUp(function(){
			$("#detailView").slideDown();
			detailOn = true;
		});
	});
});