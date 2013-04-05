$(document).ready(function() {
    /* attach a submit handler to the form */
    $("#omnibar_form").submit(function(event) {
        /* stop form from submitting normally */
        event.preventDefault();
        /* send the data using post */
        var posting = $.post("/results/", $("#omnibar_form").serialize(), 
            function( data ) {
                /* put the data in the result div */
                $("#results_div").empty().append( $( data ) );
                
                /* make the course's data show up when it is clicked */
                $(".course").click(function() {
                    var course_id = $(this).attr('id').split('_')[2];
                    if ($("#detail_num_"+course_id).attr('class') != "detail_shown") {
                        $(".detail_shown").switchClass("detail_shown", "detail");                        
                        var detail_id = "#detail_num_"+course_id;
                        $(detail_id).switchClass("detail", "detail_shown");
                        $(".course_shown").switchClass("course_shown", "course");
                        $(this).switchClass("course", "course_shown");
                    }
                });
                
                /* set the behavior of the "save course to cart button" */
                $(".savecourse_button").click(function() {
                    var course_id = this.id.split('_')[1];
                    
                    /* add the course to the cart if not already there */
                    if ($("#cart_num_"+course_id).length == 0) {
                        $("#cart_list").append(
                            "<li class='coursecart' id=cart_num_"+course_id+">"+
                            $("#result_num_"+course_id).clone().children().remove().end().text().split(':')[0]+"</li>"
                        );
                       
                        /* add code to send post request to save that the user has added this course to their cart */
                        
                        /* add code to redisplay course information when user selects it in his/her cart */
                    } 
                });
            });
    });
});
