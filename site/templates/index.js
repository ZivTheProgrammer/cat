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
                $(".course").click(function(e) {
                    var course_id = $(this).attr('id').split('_')[2];
                    if ($("#detail_num_"+course_id).attr('class') != "detail_shown") {
                        $(".detail_shown").switchClass("detail_shown", "detail");                        
                        var detail_id = "#detail_num_"+course_id;
                        $(detail_id).switchClass("detail", "detail_shown");
                        $(".course_shown").switchClass("course_shown", "course");
                        $(this).switchClass("course", "course_shown");
                    }
                });
                
                /* set the behavior of the "load semester button" */
                $(".semester_menu>button").click(function() {
                    var params = $(this).attr('class').split('_');
					var detail_id = "#detail_num_"+params[1];
					/* Hide / show selected semester */
					if ($(detail_id+">.detail_sem_"+params[2]).length == 0) {
						$.get("/semester/", {course_id: params[1], semester: params[2]}, function( data ) {
                        	$(detail_id).append(data);
							$(detail_id+">.semester_shown").switchClass("semester_shown", "semester");
							$(detail_id+">.detail_sem_"+params[2]).switchClass("semester", "semester_shown");
                        });
					}
					else {
						$(detail_id+">.semester_shown").switchClass("semester_shown", "semester");
						$(detail_id+">.detail_sem_"+params[2]).switchClass("semester", "semester_shown");
					}
					/* Enable / disable course history selection buttons */ 
					$(detail_id+">.semester_menu>button").removeAttr("disabled");
					$(detail_id+">.semester_menu>.semester_"+params[1]+"_"+params[2]).attr("disabled", "disabled");
                });
                
                /* set the behavior of the "save course to cart button" */
                $(".savecourse_button").click(function() {
                    var course_id = this.id.split('_')[1];
                    
                    /* add the course to the cart if not already there */
                    if ($("#cart_num_"+course_id).length == 0) {
                        $("#cart_list").append(
                            "<li class='coursecart' id=cart_num_"+course_id+">"+
                            $("#result_num_"+course_id).clone().children().remove().end().text().split(':')[0]+
                            "<button class='removecourse_button'>Remove</button></li>"
                        );
                        
                        /* save the information to an invisible div */
                        $("#detail_num_"+course_id).clone().removeClass().attr('id','cart_detail_'+course_id).appendTo($("#cart_detail"));
                       
                        /* add code to send post request to save that the user has added this course to their cart */
                      
                        /* redisplay course information when user selects it in his/her cart */
                        $(".coursecart").click(function(e) {
                            if (e.target != this) return;
                            var course_id = this.id.split('_')[2];
                            /* if the info is not there from the original search
                             *, bring the saved course info back to the right place */
                            if($("detail_num_"+course_id).length == 0)
                            {
                                $("#cart_detail_"+course_id).clone().attr('id','detail_num_'+course_id).addClass("detail").appendTo("#results_right_div");
                            }
                            
                            /* re-highlight the course if it's still there from the search */
                            $(".course_shown").switchClass("course_shown","course");
                            if ($("#result_num_"+course_id).hasClass('course')) {
                                $("#result_num_"+course_id).switchClass('course','course_shown');
                            } 
                            
                            
                            /* show the info */
                            if ($("#detail_num_"+course_id).attr('class') != "detail_shown") {
                            $(".detail_shown").switchClass("detail_shown", "detail");                        
                            var detail_id = "#detail_num_"+course_id;
                            $(detail_id).switchClass("detail", "detail_shown");
                            }
                        });

                        /*set behavior of remove from cart button */
                        $(".removecourse_button").click(function() {
                            var course_id = $(this).parent().attr('id').split('_')[2];
                            
                            /* add code to send post request to save that the user has removed the course from his/her cart */
                            
                            /* remove the course from the cart list and remove any hidden info about the course */
                            $("#cart_num_"+course_id).remove();
                            $("#cart_detail_"+course_id).remove();
                        });                      
                    } 
                });
            });
    });
});
