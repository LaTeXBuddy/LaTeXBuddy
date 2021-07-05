BEGIN{
printf("\nTeXFILT version 1.0 Copyright (c) 1994 EBTS\n\n");
if (DEBUG != 0)
 {
  printf("\n\n\n\a\aDEBUG FLAG IS ON\a\a\n\n\n")
 }
}         # pre-filter commands

/\(|\)/ {# left or right parenthesis detector
line_length = length($0)
TeXieFILE = ""
i = 1
while (i <= line_length){# while process TeXieFILE
 char = substr($0,i,1)
if (char == ")" )
 {
  pop1();            # a file has closed without error
  TeXieFILE = "";
 }
if (char == "(" )
 {
insideEOLflag = 0
TeXieFILE = ""
# start collecting characters to form a new TeXieFILE
i++;                    # move off the left paren
while (i <= line_length)
{
char = substr($0,i,1)
 if (char == " ")
    {
    if (TeXieFILE != ""  && TeXieFILE != " ")
     {
      push1(TeXieFILE);     # push TeXieFILE onto stack
     }
     TeXieFILE = ""
      while (i <= line_length && char != "(" )
       {
        # scan until another ( is detected
        char = substr($0,i,1)
        if (char == ")" )
         { # file is closed before EOL
           pop1()
         }
        i++
         if (i >= line_length)
         {
         insideEOLflag = 1
         }
       }
    }

 if (char == ")" )      # blank the TeXieFILE
    {
     TeXieFILE = "";
     char = ""             # don't append ")" to TeXieFILE
     break;                # should go to outside loop to look
                           # to look for next left paren
    }

 if (i >= line_length)
   {
    if (insideEOLflag != 1)
    {
     TeXieFILE = TeXieFILE char
     if (TeXieFILE != "" && TeXieFILE != " ")
     {
      push1(TeXieFILE);
     }
     TeXieFILE = ""
    }
   }

if (char != "(" )
 {
  TeXieFILE = TeXieFILE char
  i++
 }
}
 }
if (char != "(")
{
 i++
}
} # end of while process TeXieFILE
}
/^!/ {message = $0}      # does line begin with !
/^l\.[0-9][0-9]*/ {
  for (i=2; i <= NF; i++)
    {
     context = context" "$i""
    }
   tmp = $1""
   decpos = index(tmp,".") # get the postition of
                           # the decimal point (dp)
   linenostr = substr(tmp,decpos+1) # everything to the
                           # right of dp is the line number
   lineno = linenostr+0    # force it to be treated as a number.
     y = readstack1();
     printf("Error %s %d: %s\n",y,lineno,message)
     printf("%s \n\n",context)
     context = ""
  }   # Where there's a bang ... there's a message
/^.+erfull/ {
   y = readstack1();
   lineno = $NF+0;
   printf("Warning %s %d:\n",y,lineno)
   printf("%s\n\n",$0)
   } # process Overfull and Underfull warnings

END{
printf("\nWarning and Error -------\
 TeXFILT Process Completed \
 ------- 999999999:");
if (DEBUG != 0)
 {
 print " "; print "stack1 should be empty for a successful run"
  for (i in stack1)
  {
  print "i = " i "  stack1[i] = " stack1[i]
  }
 } # end of if DEBUG
}
function push1(thisvalue){
++stack1index
stack1[stack1index] = thisvalue
} # end of function push1
function pop1(){
if (stack1index <1 ){
 return ""
}
tmpvalue = stack1[stack1index]
delete stack1[stack1index]
--stack1index
return tmpvalue
} # end of function pop1
function readstack1(){
# non destructive pop top
return stack1[stack1index]
}           # post-filter commands
