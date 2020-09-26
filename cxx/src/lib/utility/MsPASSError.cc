#include "mspass/utility/MsPASSError.h"
namespace mspass{
using namespace std;
using namespace mspass;
/* These are two useful helper functions for MsPASSError constructors and
for inverse needed for python wrappers - there is no way currently with
pybind11 to have a custom exception class have access to members other
than the "what" method that overrides std::exception
*/
ErrorSeverity string2severity(const string howbad)
{
  ErrorSeverity badness;
  string s(howbad);
	if(s=="Fatal"){
	  badness=ErrorSeverity::Fatal;
	}
	else if (s=="Invalid"){
		badness=ErrorSeverity::Invalid;
	}
	else if (s=="Suspect"){
		badness=ErrorSeverity::Suspect;
	}
	else if (s=="Complaint"){
		badness=ErrorSeverity::Complaint;
	}
	else if (s=="Debug"){
		badness=ErrorSeverity::Debug;
	}
	else if (s=="Informational"){
		badness=ErrorSeverity::Informational;
	}
	else
	{
		/* Default to Fatal in this case as this should only happen in
		a debug situation. */
		badness=ErrorSeverity::Fatal;
	}
  return badness;
}
/* inverse of string2severity */
string severity2string(const mspass::ErrorSeverity es)
{
  switch(es)
  {
    case mspass::ErrorSeverity::Fatal:
      return string("Fatal");
    case mspass::ErrorSeverity::Invalid:
      return string("Invalid");
    case mspass::ErrorSeverity::Suspect:
      return string("Suspect");
    case mspass::ErrorSeverity::Complaint:
      return string("Complaint");
    case mspass::ErrorSeverity::Debug:
      return string("Debug");
    case mspass::ErrorSeverity::Informational:
      return string("Informational");
    default:
      return string("Fatal");
  };
}
const char* MsPASSError::what() const throw()
{
  string s2ret(this->message);
  s2ret += " I am the new what method ";
  s2ret += ":";
  string es=severity2string(this->badness);
  s2ret += es;
  return s2ret.c_str();
}
/* This set of functions are used to provide the patch for pybind11 handling
of exceptions.  python error handlers aren't able to access the badness
attribute or use the severity method.   Hence the what method above
posts a string representation of the severity level at the end of the
message string of a what return.   Use this set of functions to
test the return of "what" to convert to tests for levels of
badness. */
string parse_message_error_severity(const mspass::MsPASSError& err)
{
  string s=err.what();
  size_t fpos;
  fpos=s.find_last_of(":");
  /* Return Invalid if the message has no colon - maybe should be fatal*/
  if(fpos==string::npos) return string("Invalid");
  string badness_str=s.substr(fpos+1);
  /* Similarly be careful of a terminating : */
  if(badness_str.empty()) return string("Invalid");
  return badness_str;
}
ErrorSeverity message_error_severity(const mspass::MsPASSError& err)
{
  string str=parse_message_error_severity(err);
  return string2severity(str);
}

/* this may not work, but if it does most of the above would be unnecessary.
Hope is that err will be a pointer to a real MsPASSError and the
compiled C++ code will handle the conversion.  Problem will occur if
err is a copy created by python.*/
bool error_says_data_bad(const mspass::MsPASSError& err)
{
  if( (err.severity() == ErrorSeverity::Fatal)
        || (err.severity() == ErrorSeverity::Invalid)) return true;
  else
     return false;
}
}  // End namespace
