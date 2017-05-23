(function($) {

  /* datejs parser replacement */
  var orig_parse_date = $.datepicker.parseDate;
  $.datepicker.parseDate = function(format, value, settings) {
    var retval;
    try {
        retval = orig_parse_date(format, value, settings)
    } catch(exception) {
        retval = null;
    }
    if (retval == null) retval = Date.parse((value == null) ? format : value);
    return retval;
  };
  /* end datejs replacement */

  /* datepicker config */
  $.datepicker.setDefaults({
    firstDay: 0,
    showOtherMonths: true,
    selectOtherMonths: true,
    showAnim: 'drop',
    showOn: 'button',
    constrainInput: false
  });

  $.Autocompleter.defaults = $.extend($.Autocompleter.defaults, {
      highlight: function(value, term) {
        var termArray = term.trim().split(' ');
        for (var i=0; i<termArray.length; i++) {
            termArray[i] = termArray[i].replace(/([\^\$\(\)\[\]\{\}\*\.\+\?\|\\])/gi, "\\$1");
        }
	return value.replace(new RegExp("(?![^&;]+;)(?!<[^<>]*)(" + termArray.join('|') + ")(?![^<>]*>)(?![^&;]+;)", "gi"), "<strong>$1</strong>");
      }
  });

  $.message.defaults = $.extend($.message.defaults, {
      opacity: .95,
      template: '<div class="jquery-message"><p></p></div>',
      displayDurationPerCharacter: 100,
      fadeInDuration: 500,
  });

  $.parseAndFormatMoney = function(e) {
      $e = $(e);
      if ($e.val()) {
          var val = $.parseNumber($e.val(), {locale:"es"}).toString();
          var res = $.formatNumber(val, {format: "#,##0.00",locale:"es"});
          $e.val(res);
      }
  };

  $.Calculation.setDefaults({
      // regular expression for detecting European-style formatted numbers
      reNumbers: /(-?\$?)(\d+(\.\d{3})*(,\d{1,})?|,\d{1,})/g,
      // define a procedure to convert the string number into an actual usable number
      cleanseNumber: function(v) {
          // cleanse the number one more time to remove extra data (like commas and dollar sings)
          // use this for European numbers: v.replace(/[^0-9,\-]/g", "").replace(/,/g, ".")
          return v.replace(/[^0-9,\-]/g, "").replace(/,/g, ".");
      }
  });

  $.setTotalFromChecked = function(target) {
      var tot = $(':checked').parent().siblings('.balance').sum();
      $(target).val($.formatNumber(tot, {format: "#,##0.00", locale: "es"}));
  };

  $(document).ready(function() {
    /* autoresize notes textareas */
    $('form #notes').autoResize({animate: false, extraSpace: 0});

    /* datepicker */
    $('.datepicker').datepicker({
    }).blur(function() {
        var format = $.datepicker.regional['es'].dateFormat;
        $t = $(this);
        var d = $.datepicker.parseDate('', $t.val());
        $t.val($.datepicker.formatDate(format, d));
    });

    /* moneyformat */
    $('.moneyformat').keypress(function(evt) {
        if (evt.which !== 0 && evt.charCode !== 0) {
            var c = String.fromCharCode(evt.which);
            var $t = $(this);
            if (c.match(/\d/)) return true;
            if (!$t.val().match(/,/)) {
                if (c.match(/,/)) return true;
                if (c === '.') $t.val($t.val() + ',');
            }
            return false;
        }
    }).blur(function() { 
        $.parseAndFormatMoney(this);
    }).each(function(e) {
        $.parseAndFormatMoney(this);
    });

    /* show flashed messages */
    $('.flash').message();

    $('input#receipt_number').keypress(function(evt) {
        if (evt.which != 0 && evt.charCode != 0) {
            if (String.fromCharCode(evt.which).match(/\d/)) return true;
            return false;
        }
    });

    $('input[name="invoices"]').live("click", function() {
        $.setTotalFromChecked('#amount.calc');
    });
    $.setTotalFromChecked('#amount.calc');

  });

})(jQuery);
