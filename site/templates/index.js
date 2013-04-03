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
                $(".course").click(function() {
                    var course_id = $(this).attr('id').split('_')[2];
                    $(".detail_shown").switchClass("detail_shown", "detail");                        
                    var detail_id = "#detail_num_"+course_id;
                    $(detail_id).switchClass("detail", "detail_shown");
                    $(".course_shown").switchClass("course_shown", "course");
                    $(this).switchClass("course", "course_shown");
                });
            });
    });
});