from IPython.display import IFrame
#from pyvis.network import Network
import pyvis.network
import pyvis
import os
import warnings
import hashlib
import datetime
import colour

from IPython.core.display import HTML
from IPython.display import display_html, display, Markdown, Javascript, FileLink, FileLinks, Image

import base64
import io
from PIL import Image as pil_Image



pyvis_icons = {
            "iphone": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAAUBJREFUaEPtmV9OAkEMxn+Ip+AM+oByDg5gQPEAHsFEj8ArDyQQuQ5/jNcRSOM8bWTDtNnsTvLN0yY77fRrv3YmbY/CV69w+xGAtiOoCJQegRGwBO4gO59OwA8wA7ZeR0Qp9A3cew9Pcntg6NURBXB0eL5q6y9w2xYAo8F/awEMgHn6+QaML+w1J/S7BiDHHgHI8VZ1r1HoE/hwKjG597YpJACKgJO/JqYcUBIH6CMKpftD90CERapCqkIR/ugi+3vFqgpFWKQqJApF+KMqpCqU389UV6LigU5cZME6QGc7c2bYV0I3AW5K642uUu/f7Lbv5y4CqGuvr4GXZLR9Ty8AaLW9XjfgMHCbND94qqHQDnjwJlJ0wPGYRkw2pcnVZQ/BA/AK2JTGtXIPdR3SpJAANOnda3QrAtd4qck9xUfgDGo9bjFmvlucAAAAAElFTkSuQmCC",
            "phone": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAAvJJREFUaEPtmUvITVEYhp+/3IpyGZj4MUAMDISBUorkmgyQcssEAwwYuJX+UsTAxEBRBiR3I+UyMGCAEgZGTAgl12JARPTW3rVb7X/tb+2z1tn/qbPrzN71fe+zrt9ap4cO/3o63D9dgKZHsDsCA3kElgGngXEek++AbcDNpkB8U+gt0GswJt0Egy6JxAfwCxhizDoc+GHURpX5AL4AY4zZJgJvjNqoMh/Aa0DGLN8s4KlFGFvjA3gGzDAm1IK/ZdRGlfkArgGrjNn6gENGbVSZD+AwcMCY7S6w0KiNKvMBbATOGbNpBxoN/Dbqo8l8AFOAlwGZpgEvAvRRpFW1kLbG8YZMP7PD7LNBG1VSBXAW2FSR8Q+wDrga1ZkxWBXAGuCKJ5bMbwAuG/NFl1UBDAPeA6NKMv8FNgPno7sKCFgFoFCngK1OzAFhXp4sALOBxw7AfuBoQEclk1oAlPwOsKjg4iEwF/iXzJkxsBVgHnDPibkauG7Mk0xmBZCB28DighMt7unA12TuDIFDAHQyPweGFuJeANYb8iSThADIhCrOg46b7cDJZA4rAocCqPcfADMLcVXAaYG7a6QtTKEAMjUJeAKMLDj8Dsxv4lZWB0C+tQOpxCi2/wgsAXSTs35jszL8Vd1SvC6ADO4GjjtOvwErjdNJdZbuGypXdJ94BNzPDs0PwCdA1a33taMVAHk/BuxxILQmdlUsbJnXDjbIMFTex7NWAdReJYULIV8XgR0l50SI+Zyv38ezVgHyBOpxTSc3ng67nYUTW2tHYJaedwen1GssACXTC8YZZ3fKTWhu3wCOAIMN06ZMkhxASfUQdgmYU9Okr1lbAGRAh53K7b3ZDhOLpW0AueHJwAlgaSSCtgPkvnVv2AcsN16g+uNtDCA3pPppC7A2O31DB6ZxgNyw1ohGYwWwwPjnSPJzILQ3i3oVh9q19LI3NSsW9Qqi3whAZYX+xip9/Y55DrQCUbttF6B210Vq2B2BSB1ZO0zHj8B/A55lMccROl4AAAAASUVORK5CYII=",
            "android_phone": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAArVJREFUaEPt2kvozmkUB/DP39S4ZBaiJEouzZKyUphYuNRIoiaJkoU0LuVSinGfCVODiCiTSxYW0sTGZWPBwgZruW5IWJCEXKaT561fen/v+/vh//4tnrN53t7OeZ7zPef73M7v6VJP+mATFmNwPdO22o/xL7bhTVvtpNBVVTHpncWvOI176b+JmIBdNftah6u4kuxGYi7OYXbVvuoAmIYLWIaDhQH+wHZEdqpGrjdeYyP+LPS1HPsxqQCsJZY6ANbjL/yEl4VeG8Au41bFyP2MyQjbSwWb6PsF1uKfKn3VAbAFm9HMZhUWoX+VQVMAjmJvE/2P2IoYr618KwBtB6qhkAGUBasVhWoEuK1qzkDOQFuStFbIFMoUyhTKO3FzDuSNrOLc6LFldAbiSB3n/FbSF7+ku0UzvR4BMABP0vE4zvKtZDdWYiCef0/H6UPprjwmORUXliHp98OUnR9wE0fwewnKHslA+DIID5JT/VL7NrU/pvYVwsHhePY9AQiHD2MBbqR7bdyfI/IhQzE9UWcsjmNpyXzpeAaCFucxBVFp2IMPJdHthTXYke7CM/H+M92OAwhnwvGIfpRbQhrU+RxHg0rzUhaiIhGViaJ0FMAw3MYJLMExREYWlmTgJN6lAkAUseZjVIFqYdZRADuxOk3KR4jiVBQK7pQAGJ3odTfNi/v4GxsK+h0FcA0xgaOs8iUSZZWoMY3vKQBP04b0Jc43bGI5jSW4IR3NQPB3xNd4n2qsRcp1FMBX+t7UPAMoi2q+D1TkW6ZQplBFqpSpZQplCmUK5cpccw7knbji3Oi2ZbTsQ3dFvyqpdeuH7qm4iHgOcKCSO/WVVmBfdz01CHf+wyycwfUmJZH6Ln+yiELAOMxJY0RbSep8qY8O45FGlEF+Q1zQ69q3Oj5EdeNUeo9R9dGI/wGc8+AxN859iwAAAABJRU5ErkJggg==",
            "computer": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAAVBJREFUaEPt2L1KBEEQBODv/MtUFAyNDQ19A00FQXwOI19CfA5RMDUxNjU1MBIzRdDQXyZb1tNl6eHu5pxNd7q6q6tqYWeg8GdQ+PwqgXErWBWoCgQ3MLUWWscJtrEYXFK0/BVXOMJtG2yYAmn4G6xGO2euf8Ym7pu4wwicYy9z81xwZ9jvIvAyAbb5jXCabbmLwFeretxB/3OeYcNNMoE020zJClQCub4mfXCali5egU/MlpyBSqCPd3OdbWageAU+MFdyBiqBXL7ug9PMQPEKvGO+5AxUAn28m+tsMwPFK/CGhZIz8D8ITPJP/SPWuix0gd1cCcyMc4qDLgIbuMZK5uZRuCds4a6LQHqfbueOsYOlaOdgfbL0JQ7x0MZK1yrta5Rgv9GWVwKj3ffPblOhwLiXGOo/7ovb0PCpuBIIrzAIUBUILjBcXhUIrzAI8A3a4lUt8M/XawAAAABJRU5ErkJggg==",
            "email": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAAylJREFUaEPt2U+IlWUUx/HPCCa4qCgVNYLAVmkkuDATAnMRtEqsCKlwUeKiciHqInGREjNWC7GFoqSgSf4BN+1EcVVBizYFbQq0psY/IGZIaJqc4Xnj7fXeO/f9c+fOwH1W9859n3N+33POe84z7ztkmq+haa7fAKDfGRxkYJCBmhGIEnoAO/EmFtS0N1nbf8cR7AiAYWybLM8N+xkJgKDJIv8X3sbxhh01Ze5lHMZDyeBYAPybvhzDuvR5D7bgdlOea9qZiY+xqag1DxCfN2Bvui++w6u4UNN53e2PpYpYiX+wHSNZ4IsA4WwZTuEJXE1ZOVNXRcX9zyfx8/EbXsM3ydZ45bQCiL8/ii/wIu5gFz7E3YpCym4LXe+nsonyOY/XcSlnqCNABrcVH2EGvsJbuFZWTcnrH8TnWJvKZDc+SIHMm5oQILv4pdRzH8FFvIK4P3qxlqbyXYQ/sR6n2zjqGiD2P46TWI6/U3oPNEwQg3QfZuP7FKhfOvgoBRB2ZiHSGbUZKybhRtysCVLVbmmATOcb2F8iUp34ipl9Dwe7DEhlgLD/TKrVJ7uo1XZ68vdWzJqYOWXurVoAIarbblEEiBbZRHerDZC12on6dR5gDo42NF8aAQhx8/A1ovXF+jVNzG8LoX8WJ1JHi59+xnO43GXNFy9rBCDEn8Ni/IAbWIFb2IzPktd38Wk6YwVslN8S/IgXKkLUBiiKDyHX8Qmim8SKE26s4in34QReB6IWQIg/m6L4E1ZhLJfjNTiUO7fH/xnv4MvcNXOTjacRNiIAf5Qop8oAefFRNuH4SgvHT6UDYRwGY3aEyOIKiCjByETYWl2inCoBFKNWjHyJAP53adVMlAbohfiMogpEKYBeiq8K0TXAZIivAtEVwGSKLwsxIUA/xJeB6AjQT/HtIIodry3AVBDfDURLgKkkfiKI+wCyCZuN9iaGVJXB1mpPq8COHzvyz4VilGcjvd3xoClBVewUjx2hdRxgFAuTxVYHsyrOerUnn4nwMTrdH68PZy844rFhPJfJMtGrCDZl938vOJoy2hc7g7eUfQl7zukgA4MM1IzAtC+he95G/fsbH43cAAAAAElFTkSuQmCC",
            "person": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAAydJREFUaEPt2U+oVVUUx/GPGSVCfwwUSiQHRaMQhVLBgWCGRlkURIPQgRNNESOoUSooQhaRKYLQKPBPSJkpCQVFSP6HiBAUnGhEUFhkgRJUsuQYvvvOvfecvbfeJ7w1vGevtX7fvc/Ze+11x7jFbcwtrt8oQMcKjscLWIRpeKB6/hO+xz58gkulVr7kCizGRkzuI+483sDuEhAlAMbiPaxsKeh9vIp/W/oNGV4C4B28lihiA95M9L3qlguwAJ9nxInZfwJfp0LkAhzFzNTkld+3mJMaIwfgcRxLTdzhNwPfpcTKAXgdb6UkrfGJb+jdlFg5ALvwUkrSGp8deDklVg7AZ3gmJWmNTxxwz6XEygHYj6dTktb4HEidjByArVhRCGALVqXEygFYjm0pSWt8lmF7SqwcgCk4l3GIXdP7H6YiaqTWlgMQyQ7lHEKV2m8wt7XyyiEXIBInlwGVhnn4alAAkfdjPJ8oYA9eTPS96pa7AhHjHpzAwy2FnEGUIxdb+g0ZXgIgAsbNK6rSuIU1sVNYiB+bDO41phRA5LgXm7AUt3VJGuXzB4g66o9c8aVeoU4dj2IJ5uPB6mFst1/gQ/xQQvi1GCVXoKSuxrFGARpP1Q0aWGoFJmFWtS3G1ng/7sOESvfv+A0/43h1k4vr6K+5XDkA46oSOPpBcbm/vaWY2JGOVB/2TvzV0j/5ILsDr1TtkJjlEnYB0WKJ6vbvNgHbrsBT2IyH2iRpMfZsdS842NSnKUB0397G6kLlRy99UV7HBT/aj//0A2kCcCc+wrP9ghV+vrdqGvR8pfoBxMyH+Og4D8KiWo3OR9f+aT+AdVg7COXX5VyD9d009AKI/fwwYhUGafEdxBlzsk5EN4D4PdqGjw1S+XW549Cb3QYgavWo70eSPYkvOwV1W4FPB7Dr9Jus2JWGXV3rAO7GL4jtcyTZZUzsLDnqAKKuaXwS3mTCYa9RHUDJtnlpvtAWFcH/VgcQf9ZFr3IkWvRih7Qz6wCiw3Aad40wgj/xSHWn6LkC8XB6tQpxDkT5PEiLWiguQdG9HvY3VL9SYpDCG+UeBWg0TTdw0BVsrm8xtFOqAQAAAABJRU5ErkJggg==", 
            "home": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAA5JJREFUaEPt2WmorWMUB/DfJUOmkqFkCpEhIRSSK/MQGW6Re02FEBkSiQxFkQyRQlFCZCqZXfMH85AUiWuMDz5IiMz6s15t5+5z9tn7vGefXfbzZbd732c967+m/1rPO8/srVXxQIk/HN/PxlHzZkMoVsLj2K3kv4j98WPb580GgBXwMPbGu6Xw1liMg/BzmyDaBrAc7sfB+BDz8TuexxZ4Aoe0CaJNAMviThyJzyt8Pitrr4uE0cZ4EEfgtw5PrIkNu3jmE3wzlcfaAhA5t+AEfFnKfzzh4A0KRBS9A8fhj3rnJNzcRdGjyyiTYmgDQGTciFPwNXbH+5OcuClewDq4rQD/iQZALL4EmyGAhwLgSpyLb7EH3u6RpEno57AGrscZOAp34XJciGtw1jAAXIYL8B32wuvTrDDb4lmsjsi4qEIoHhwagLNxddX21PgkaT9rJzyFEF6MEE/uiFeG4YHTy/0/4cAKiX6Ub97dtUrryhWGV9WDWQ2h43ErfsVheHQQzTv2hPBCfMvjVNxUYRWvtJ7Ei3A7UjmSePfOUPlme8jtPoRLTsTdZZgYKtzSShk9tBReBsdU1WhJ/7/FLMA9JTCGimdDfO+0AWBfPFRuPrlIq03lG1nHFj+k/UgHm9Cack2HyPbEI1gR51Tl6SV3Js9Pww34pfqmdLUDh9DOVepWwfm4Yiaa9bH3TFxbJfqAYu+u26fywHZ4psjmUlzShwJtvJozQ3AhyVSq17oJnQxAJ91fV7TehlL9yojHz6s2JaH81kQB3QBsg1eRwSRNWkgrZXOuVtg+rJ+cSEj/B8REAJvgZaxVbXE6wqblnSsA0TFzxfo1G+yCDxplOgGsV/3MRvUwfUrK5yisJ7FPKfJFzRuf5n8DYO3K9M3rN6NgNu03CtpXvxRjPl1d70c1rn4VABnnMrNuVYP3xXhpRAEkB9Jup4FMGM0PgIRKylRApOZuiTdGFMAOeA+P1eS3OADSuiZ5F+IHbD8AgBBdbiT6Welmc950Vm4zEkIB8CZyXia4Jd3K6CAAmgOmo0zzTj85NhHAv+e0DSA3Er0ursIvuWYZSQCNi6fyxEw8vJT8tj0wBjCJ64aWA2MPjD0wIJFNGqNdLDquQp1GGZfRssY4hHo0UWMe6NVljkNoHEIdFmiVaMZE9o8F/p9VqJ+huxnqcxGbu/2pVr7CrFafqKY71Dfy+5rIepXOuXi+FIC/AC2dTp/TMnsdAAAAAElFTkSuQmCC",
            "cookie": "data:image/png;base64,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",
            "bank_acct": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAAf1JREFUaEPt2MurTlEYx/HPQUSKAZmcMjIzUIYGBv4FZpIwPLlEUi65JyaUgQHRGRuaKGMjUykTMxMSMUEu7VrqnG2td6+9z97tc97WqnfyPmut5/k+z2/d9owV3mZWePwKwNgVHLICW3AtAF7ExyFghwBYgyO4gQqiap9xC3fxvU+QvgH2hSB3JoJ8i9N41hdEXwA7QsYPZAb2AifxOrN/sttSATbhEuawNuLlW/hvY8T2A/dxFV+6gnQFWIWDuI1tEed/8BRn8BOXcQzVuHr7FCAqmF9tQboA7A0635Vw9gon8LJm34172JMY9wan8LwNRBuAWdwMmY+Ne48reIjfiSCqcftxB9sTfaoFfhzvckByADbgbPitT2j5AS7ga45T9DbnJIDesxWBW3JVUwCD6HVCdbquq+hl7gkOEbV9CFJ51GXHaJDXahzFdWxN7GzzOLzQFqtAtQXWW7UVPsb5oe40Cxxuxrlw0K2LxLIo5hyA3k7NzAX+r1vqdG8N0NLv4N0LwOApbnAw/RWoJ6C+K9UXfpN90PlyrhJNATbZC8CkNVEqgCKhmkRaJaRIqEjo/2t7kdCgB0+G5EoFSgUarsNNEmmyL5q+nAMZi3JQSeY86sd+gdX9T/+LLPZdaDlVYforsJyy3RhLzjbaOMmYHQrAmNmvfJcKjF2Bv/hFkzGQayKYAAAAAElFTkSuQmCC",
            "business": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAAOhJREFUaEPtmd0OgjAMhUe8wPd/Wr0wEg0kaljo6dqwmY/rs9Hz026BqQz+TIPXX/6LwGW+Ps9w5HG/uYX8WggBp304sAlHhHqNUC2jNcei8BY9TFMoqiCVMAQ2BXBgVYII7TSFqYktzdSC4STmJG7JTymFCBGhnwhFHXyWZKaMUQhYpF8xOLAnFhE6O0LC+13QT4dTesBVlbAIAoJYKVAcSJFV2FR2QJ3rQi1vqLo/BKKv3zhwpKiqED0gfAgzXSWyHWhxDAKqehH47s4BlRQEjsauqqiKrzqgbtQD3v2Lv4fiXzUMT2ABkT84QP0nyTMAAAAASUVORK5CYII=",
            "wallet": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAA0BJREFUaEPt2VnobXMUB/DPNct0M6dQMly3lKSQKUNIhlfKi6tu14MHN17kQUmSyCOhiHjwhkyZifJiyFwib4YMGTKnr9b5t9vOsfcf+/z3qbPq1Gnv3/6t73et9Vu/9Vu/dRZc1i04fmMgsA12w7f/xphrQWBvnFm/o7ERO+NTbMHjqyEyDwLb4wScjbNwDGL1iXyPz3AIfsCB+KYviaEIHNoAfFqFyATTF3gaT+ElfIw/8CAuwoV4eN4EdikrJzTOr7CYYPgdbxToR/FKAW5jvB7XVhjdMTSBbXFshURC4zhs11D6YVk4Vn4OCZMu2YpbcA1u7Bo8eb+aEDoA5xboM7BnQ0li9tkC/SQ+6QugMe5K3FpeuKHv930InIpMfh5i+UjC4rWGlfP/t75KZ4z73wkcjNtxTimMlR8q0M/g6/8IuP35SWWkeDBh10tmeeD4ysfrKz/Hpffjx16zznHQNAL74D3shXvxKhL/O84RV1T9XCn2MXw+S/c0AjfjKryJI7HDnIG31f1U2em6aetsGoGkwMNqlnx8H97CL3Mmkh08pcYl2KnWXza6bHorMo1AgObjuC3p8u05A2+rO6ISx0G4vBLLTAJ7NOqQVW3pA5M8ES/jI6RMmUkgLnu9wmXei7bLBh/gcOxfxd9f49shlLLgCXyH3btmnPP7F3Fy1VnJklMJZEAGpjbPRjYm6UUgafPdKnNPGRP6MmynB5YEBvTaMoQGNG6vqRfGA6kCUi7kzNGUhSCQc3EKyYDP+fi2BoPRE0jafqEBOF44qtJ6Ho+ewCbc3QqbC/BIPRs9gVSb72DXApxqOPvSV4tCIDjTtbsCv9YhJgXcREbvga5cuiTQZaGh3y89MLSFu+ZfeqDLQkO/7+WBDdWVSwcgp58xSS5D0j/N5vb+BFj7UL9vnfj/1r4YAZNgyjVUWp9fziKQ55P2Ra6Gnh8B8EBIgy3XUrF8PLAi0zpzl+Gu8sTFq2l1D0T2dDyA/XAp7ukiEFJ3IkQicV3aLO0DxkB4V6bNZUpaOwmbSDBtbiuddT+Q52F7NbKw11ISNje1Lf9Pa6ANNosmN+lrIekQ5lp2pvS5I1sL4L11Lgn0NtVAA/8Ek17UMYWeJvgAAAAASUVORK5CYII=",
            "encrypted_email": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAABWlJREFUaEPtmXeoHVUQxn+xd8USCyqxYI9gNwoKYou9t6ghgh3s2Ind2EIwttiw916jiD2iUdQoFkQURLEFCyQak2iUX5gT1s3ee/e93XtvHrz5J3n79pyd78zMN9+cN4A+bgP6uP/0A+h2BPsjMC9GYBBwBrArsBqwUIed/A34ELgDuB+Y1ez7+RQ6JBb6/HngK+CfDgNYCtgBWBd4BTgAEFShZQHsBIwH5gdeAvYDpnbY+fS5PYHHgAUDhL4VRiIB0OnPgL+BW4BrgE8BN/q2wyBOie+bRo8AVwKHA/cV+ZEAbAe8DphCDwE7Aw8DfwJ7A+91AMQCwHXAccCjwHBgGvAJ8D1gFOayBOAk4FrAAv4m3toAeBZYMTZz03bZMnFgOnk5cD7wb3xsLDAMWK4ZgAuAC4H5Mgt9fwXgSWBIbOrmddtawDPAmsAxwN25D+iX/hX2rPSw2UsLA7cCRwAPAiOAv2pC4cF4QKbP/sBrBftWBuCeAj0zwvsOsC/wc0UQBwN3BklIFl802K8WAGnvA4G7gB+APYDPewHCwzAlRgIvA+75e5N9agXgd7aOsC8WrGXDK2uLALcDh0VangjMbLG4dgB+b9UovI2AU4HrSyBYOYBvBpwX/F5i2WxyqVTEjT6yZGgVU8nm52naCItscACWCj19WaestQ2ADsge1oROPRf94peMZ+a7HH5TSBRZ56Oynsd7bQWwZZymmmWJ0E5PRPe0h+wIbAH8FA3RZnhkdNiyONoGwNSxL/wIDAUWj1zdBVg0vFPN3hxd/nTgMuBdYK8e0HBbANgxbwjdLpBsT3B+WAn4A8imk5gSDQvadQrIlIrrA5vGWuWzeyqnT6uziM3pS4JF1EmKPx3tiW0FPAXY4U2ntYPJHJ7yJsX+GunXaymRNjXPb4uPtmKdVoAUjc4cOq9oezrS8e1ISRluDWB34GhglVCqToozspuX0UK+74YOGBalHfTSVh62+P22wIvR0WUp60LbHpAYTD2j5L82TOtA518A9smCKANA9FLkhnEa0mYV82QdVixw5bMp4kDl/HtQZmOfq7neiGdHRQaMA05I77UC4EygVFg21KJhr2qe7DbAJsB3sZmFOjpYymlwnQBk5FcHpsd7V0UkjNSbPksAzo3FhsspSHNKU+r6s7k4qarnwOYx3Tk2OkBpyhHTc3lAB5PJSEbkolDB5r5U/SXwcdyazAHgzHkPoE75IBY6WBjm3TJTWlUMnu7xMSg5rioxzH9FXjO7N+YR37k4WFCqnpwi4A8O7+pzJfLVwIQomIZXGr1A836wjBHVzgZGAQo9e0ORmfPOx6k5SsPOJA5Aj2e59cYYqH3mQC9Hp9zrha+FS2xOdm9ncK2oy9rspNNUH/l3TLXJUQujswDM/1eDxhwhRW6nrGt81GHvdrwmOacJABWtTieqzgMw3axL63ZUvrsJwvSxedi4emLe4B0adznSpBcA3utYcOZ6MtPUubpRBFoBkIa/jloa1+h2emBwtC+rMsuYLGGHNvTZNFBqbxwbOPvK+etVSCEbn0XtZDix09frXlo5G0iRRuks4IoSRWw9mh2aw5ASXe00s9MAvMCSmicGPdvdZSaFXTOT4gVhA5QdrQ8lTVf+xGQTGwOkZiYIry+9lc6bQk8ieQBYOnqGYJXeU7oFwKgrJ2yQDjmpIzeLgHLCNdaO+skozLZOp1D6rlQoQznUqDC9pVAB5E3pcGz8XlZ0/vjfNU63AOio97Anx7RleqhxbGDOzwJU0Cna/L9XjirQuS7SugkgnbbOKxWUF/aLNI56S/5WaLQ5KZMP0bwAoEyPafhOP4BKx1fD4v4I1HCIlbbo8xH4DypJN0B55BUEAAAAAElFTkSuQmCC",
            "ip_address": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAA/JJREFUaEPtmUeoFEEQhr8niop68CBexIBZMYEJI570YMAE5qMREeNVPRtQMHsyCwZQFBQEM2YUUTwYMFwMB0EU00H5ofvRO0zv9OzOzu7CK1h4b6a6uv6uv6uraxqoc2moc/9pAlDtCJYSgdbAcKAT0BFoUSaIP8Bn4ANwH/iVxl4aANOARcBEoE2aSVLo/gAuA4eA8yHjQgCMALYDo0IMZqhzC1hrouI1mwRgBbADaB6x8Bx4YkIvCpQjoqCoOBjoHzH0F1gF7PVNUAzANmCNM1Dc3AXsA16X43GRsd2BZYAWrpWjJ1/WxY3zAZABOWvlDjAHeF8hx6NmuwAngZHOi+VxkYgDIM6Lf5Y2p4CFwO+cnLfTKAJHgFnmgeg0Gnjg+hEHQM5LUaKVn1AF510QV51IyB/59s8qRAFMBc6Zl+J87xxp4wtwV+CFsyemABd8AM4C083LLcCGnGnjm85NKGccWhXUQjphvziHlDLCmxoB0AN4aXz5DnSwJ7ZLoXHAdaP0DBhQI85bN3T29DP/yNeb+tsFMB84ahSOAQsCAciGxko0zm6wZsBuoL059Bo3HvAVuAs8DZxDaseBuUZ/HnAiCkAHhXgv2QqsDzSuFHvY6KpWUuqT6MBbkmBDgJXfvwXMJZ9UWkjkq/ZFQQQ2ARuNwmZA/4eIb5ybEIrZCY127DwuhbIG4Nq7bQ5HC0SluGhg5x8UQKeqAoiLqPab3Tui2oGEcNc0gMXAwVoGcAXQz8pAk1FqmkKhm1hUUiZLktwpFAJAzqt0D0mjuQMoloV0IboXkHncqFQVQJpzxUelJgCpVsac5KWc7KnmyeskzoVCKpRUMEm8XYCY5fEVc77nSenS99691MhX9aoKijnVJiqsJCpd7TGfNKGvnPY9T7Lne6/yWZ0RicpqdS0KANTThWasLQ7dPdDSXCnbGZS9nGtcqauW1bigK6Um04V5Rgn7ICtHfXbE99Xm5WlgtlWMtlXUsrBdYbVV+gDvKu1dgv1upq0ihkgmAxd9APRcl+UxRuERIL79rBIIdeeuAeoWSm4A411f4jpz+nih7pz9cKGQKSWm+vCQAWA5r2JvprGl1qJa/A+TAOi9OsR7HEV1EJS63mbgWIgJ0UZpUotpZSmwPzq4WHvd7QJonJq7apOoV/8qxIsSdHqaxVOnwnJeZrxdkqQPHIrEzpjvYOpVPgY+mV8JvjYO0ccN/YYAfSOGRJuVcStfbBNHnRlmSgtt5jxFG1YlQwHn01AoqqsUq8bVJKBthZCo73nJfORr7EAXmyuJQnFjlR2GAp1N6BX+ckQ0/Gg+s2q1U2W7UgCU42zmY5sAZL6kKQ3WfQT+AzCrB0ALf1VlAAAAAElFTkSuQmCC",
            "empire": "data:image/png;base64,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",
            "r2d2": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAABT9JREFUaEPtmV1oHFUUx8+Z2e+5s+kmTdOYNGGhGz9qsWqID0Ibq0V80JIKSsmDBj/qi4L4IvjsiwgVi6DSSB+kHwHFtvigtpWiYKmsYDHYZmNxk9otaz537mx2ZzJz5O4mcZNssuPumk0g92nYufec/2/OPffcexdhgzfc4PphE6DWEdyMQLEIEJGcTqf3AEDL3PtbgUDgV0S0qh2xqkZgenq6XpbltwGgDwC2LhGbBIB+0zTfC4VCU9UCqRqArusP2rZ9FhF3rCaOiG7LstwTCASuVgOiKgCc8wcQ8UciYguirlwBOHUSoLsboOfQIq2IyInoUcbYtUohKgYgIk86nR4kop2LxLz4AsDoCIAkAZz/GsDnW6r1hqIouxHRrASiYgBd148Q0cfLRHxwFOD8OaD7dgF+eAwAEYgIEP91iYhHFEX5tKYAnPPLALB3mQgigEQCoKkJQJZhbGwMNE2DcDhc2PUyY6y7ZgBEhJzzGUT0lhJhGAZks1lQVXWhKxEZjDEfIlKp8Su9r2gK/RCnkGFmL5TrXIxLW8aTT98dHCvXRkUAh76gZtum2+U6F+MkCXd8+SzeKtdGRQDvXqGmeHL2bLnOxbj2La6ed/ZiolwbFQHout4sClO5zsU4Itqmqurf5dpwDEBE7kQiMQgAkUwmAz6fTyyJUVVVHxbOk2kJhqckRzp2brFgWyCft6lU6hcAeGjeJgDEmpubdzmtD44B4vF4yO12TwinBQCGqqoe8dv3oy7o/y33WLK9stuAfa2zuX6aphmiGBYAgG3bW1tbW8dLGgJwfqApBfBTwgWnrrud+ITee014ZPs6A3CkvEinmkRgXgciLkyha2MyfPOnyxHHU+FZuL8hfzSYBygc+L9PoWIAleZAzQFuTkvw8x3ZUQS6tlsQrrPXNgITExN1mUxm0UkKETOqqi7bJzuimOukaVqWiBbtpUzTrG9vb590YsfxMiqMjYyMnAGA58QzIsY9Hs8xRVHeL+bo9wkZRrV8XdjXaoJ3heDouv6WYRhvEFH7nJ2Btra2552Iz+lw2lH0i8ViLwHAcfFMROdaWlpeE5V4dnY2VxtE8/v9IMsynBh0w4WR/LL60f4ZqPMW33CKSpxIJI4j4jNzWl6ORCL9TnVVBcC2bRDbZdG8Xm/u0LKhAEzTXBQBl8u1sQDEUVFEQHx5IV6SpI0FIMTPzMzkphBjLJcD38XdEE3mk/j1PQYo7nWeA5aVr6wiAoUH91LJuC6SeCWRyWQydwYWK9NKraYAkUjkMOc8hYjLVnmxMg0PD0MoFILGxsai+onIZIwFY7HYmZosox0dHQc1TfsEEV8tplBAiIReqdm2fSIYDPYNDQ2JK8m1rwMCIBaLeW3bFlW5SQgWVycrTZn5WuHxeETSUzqdjnR2dv5RUwDxdaPRaB8RfSaeOee5RBZHzsImltrJycnclJpL8q86Ozt7RJ81AxgfH7/o9Xr3C6eWZaWDwaCKiPbAwIAcDod7UPwBYFn+TCbTpijKjUIAwzDqLctifr9/RPxu23a0q6vrprgc0zRNkyRJEb9ns9mLDQ0NT5RavebfO95KEJGPc34HEesKjB9gjFV0scU5PwAA3xbYnFIU5S5EzBeWEs0xAOe8FwA+X2LvNGPscCknq73nnJ8GgKW7z17G2Ekndv8LwCUAeGzJvBY7uNZy73VSqVQDIv5V5G71EmPs8aoBiDshXdffLLb9Fv/KBIPB606cLe2TSqXukSTpYJGxpCjKUSd3Q44jUI7AtRizCbAWX3k1H5sR2IxAhV/gH7Y9EV5JNEShAAAAAElFTkSuQmCC",
            "coin": "data:image/png;base64,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", 
            "bitcoin": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAABXhJREFUaEPVmkeoZUUQhr9RMGFAx6yYc0AMKGZQTKiII2YxgJgRXJlRxLQSQYwgIpgDRsyCouhGxYhZUXRhXKgYEeV7dA99e7rP6XPvfeKrzdw5p7u6/u6qv6rrvHnMcZk3x+1nWgCWBXYH9gC2AjYGVgV8rvwCfAd8BLwLvAi8HJ5PtIeTAHDu/sBJwMHAUgMt+R14FLgNeBr4Z+D8meHjAjgcuBjYepxFC3PeBi4DHhyqbygAXeNGYO+hCzWOfxY4A/ikcfygEzgWuCnx63yNT4Mr6NvvA18CP4dBywPrAJuFWNkP2KBipHNOBe5uAdFyAo65EjivoPBv4F7geuCVlgXDGHXuDJwFHAEsXph7RXDTztjoA+D7G4DTCgsYeGcHZhlg+yJDNwWuA/YpKNFdz+wK8D4A7vz5meJfg+G3TmJ1Ye4pwLXA0tk7T+Ki2lpdAPT5O7KJ3wIHAG8UFB4E3Bye68OPh9+15yWbdgCeAFbJXh4N3FOaUAMg22hkTETO1XgT1YeV3fgKWCu8+xpYO/yuPa9tqi71UgbiJ2A7QKIYkRqA5zKq1G3MtKWdjwrzYIu6a8+7PNCTEESaHJ8BZK9eACap+7JxJwN9Pj9NAC6vG0rbqSwAHkof5Cfg/9/KMmwRORB9e82urSy8+xH4IGyIMfZnx/wnQ7kSh2jbtikr5QAMUIMoijy/RYUqU98eiGHhcDOuG1GLq82Bd7I8oY1PRQ05AF1HF4pyJ3BcxbppAFD158A2SdbOlzMjH5U8lI1kpRlJAcg4lrxp4OwCvFoBMK4LldRdGLJ96d2uofSO734DVgYklhEAuftIWdJpa5nbyjarA1cBJybWym7bVzbKTdaW9ZP3spGxOQLgauDcZJAlhGm8VVoBqG8l4IdEsTy/QsdCspGsFMUNuCAH8FgIqDjomNaKMEyYTQB5VeBF6JAcgEywSYJSunqzdfsLrlZLkmsAnvbxjS7kMLPw68l4aViGGnEhj9SjjWKgpMfch6U1Vkp6dAfdoibaIsFE+T6WGuku/QEskQxasifJ5IuNC+CzQKNe/GuiLd6ho2jrDFv+HwD05QHtbALgscxPUPrbtN8q456A+rvygO+bXOi/CuKheUAAeRB757bEGXGhnEalrrtat38AC6lyxex0+/JAE43KAunF3fuoLY5Wmc08kCcyr7q63cgJ2GWzfI0iO2w0C6XE0Dwg0WjLeoltxVKiVMxZSNXaJdMs5rrywG7hdhbtrxZzDrDHY58mijGg/5VkWuV0Xx6wfD4yMcDy2jJnRvJ0n7uRF5otKxeOaQD4GDgQ8N+SyDT2TdPGlzbakyoCEJA1h3VQFPuV+xa0j+tClifSoHdsL0x/VYz38fPAXsl7azMpdSFhlAquw4AHMqWWsrd0LOSraV/qTw9dwXTZQ4GH0we1itHLQtrqM3DsCb3WAWKaAHYCXshuh96DvXSNSA2A9OktablktNWgvaHZbmzZwbYnZPkQxUSnWxvwTQAc5MU5z8R25wy60klMo7W4Y2hJ5q1FmfH+0un3NXcvjxkvmaw7nZP0QXtCo/m1Pn9N4VOVX24uqWnpA+B7e/8qz8X2o+11GWUSkSptr6dsE/W5tt8QqtIHwImOcRdKLW7zhL2k+IGjtaRWp1le4+xDLVawsHPn4/gWAHGszSXb534uKokXE9nLAPRUvkiaVZLBuuEeKxFYy6S1TarPgLUXW/T5IUFcMnLDwM2lxDaJG8W5UqWtnEXYZtwYqM0zoRhYtgSnIWbYS4FHhiob4kKl09MVTgg9mvzTUJ8tsplZ9fbgeq3xM6J3EgCpomUAy949Q/Fnf2m17E8Nvgld7veSPzWY6W9OItMCMIkNE82d8wD+BdORLUCV/YJKAAAAAElFTkSuQmCC",
            "criminal": "data:image/png;base64,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",
            "shoes": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAA1ZJREFUaEPtmF2ITGEYx///d8b6XBT53plzzoyPJBeWC/kON4SSUqK4VTY2Fy7cywURSSTkxrVESqySvRK52C32nD1nWKzcaBOZmffRKNK0s+/MOXNo6pzb5+v/e573nN7nEC3+sMX1IwH43xNMJpBMIGIHkiMUsYGRw5MJRG5hxAQ1J5DP56fqYvksoKc2VoPvvMA/DkA3FhfOuzaAZW0QQQ8grwGO1E4v7RpMV+wKmABgnoha5xW8p+EkNRY1FsBGETwmsWnA93vqSWtZ1nSl5SPIS17gd9cTE9UnFEA+Y+/Q1AdGK07hVkC+uIXABiBRBZriQwHYWes+RTYJOVRdQAETAcyF6JVuofDcJCCqPTSA0pjuvvVXVwuwbXu20vIe4Ck3GDwZVaApvukAlYJ2xnqmKDPcIFhsEhDVHgogl7XvArLdVFxBlr4Jgn6TXxR7KACnw1mlqHdDjb4QaUEbgWMiOOEV/NNRBJpiQwGYklbs+Y7sSwG/jfae1BNfr08sAIuzWbskfABiodboSSnpHgiCF/WKasSv6QBOxtki1LeVSAnEVQiOgGynxo2ikpNBEHxoRKDJt6kAToezEqrcS/IFi+ndkiptE8gFkp8FMgvAdwX0aKhhRRmCyCeQ7wAMa6X6Pc/7YhJcbW8ugONMg9b7NHA9BZyGoAuCe0Xo/W1UZwQ4JMAQRcaBrABVPfIKwmvjp0y63NfX96MemKYC/F0wl7UfArq3TJ6h1jcU1S4C10vEYd/3v3d2do4bGR6eVVZqjiA9l9BLQe4EZA0E/YTeM1Ao9JkgYgP4XdjJZm9BsJdU3W4weNEkyMlkNoPqpgATUqLXmyBiB8h15JaBxfGN3Ivy8/MLdLrYS+FIWWFFZWK1wGMHMHW8lj1vWb+u8xB2uYXBCy0HUBHsZKxHVJjp+v7ylgTIZawuEOeRTs12XffTaBDGIwTiimh4YY9ClDgCS0AcHGu3MANEUdCk2LHWWiMAhTt/oPxPFvRq3jak1grlTjSABpb6JjX8T5rfX6KwAHX+Vmm27L/zSTvARSQ2Dvj+k4ZeYsdxprGkzwllcpwSTbkp/CppdbTWRS/5N2rqYNz2ZAJxd9iUP5mAqUNx25MJxN1hU/5kAqYOxW1v+Qn8BJgHv0B0hY/aAAAAAElFTkSuQmCC", 
            "cloud": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAA0FJREFUaEPt2FnopnMUB/DPhAjZJmO/YIipGbuakS2yZIm5MFMzNc3MjUxmZG0u54ZibJEISZElE7KU7AaNiaGGXFiSJUnZCReio+Pf6+993nme9/c89K/nd/m+Z/ue85xzvr/fNFP8TJvi8esB/N8V7CvQV6AwA/0nVJjAYvW+AltI4a44Fgdge3yLz/EqfihOP50tsnlYjTOx9ZBAf8OzuBobSoC0/QlFlm/BMnyGu/E03sXPmJ7VCGBLsD8exAX4cRwgbQKI4CKrs7EG1yMyXXW2ycCvwUc4K0E3wtEWgG2xHofgbLzSIIoj8BS+wnH4qYFuaz0Q2b4Yp+GFJgGk7FGZgIextIl+0wrsiRU4HpH1D/EybsMN2bhN/A/KXoq1OAZv1TXSBMA5uC8DDwfRpIfhYHydzVkyGiMh7+N1LGwbQIzFlzIzMT0+GHBwMvbBvXWdjpC7Fhdid/xax17dCmzCbjg6s13H9jgyp+A5nFB3ENQBMAebs0lvHieqBjoHZnUX4/46eqMAxAaNBXMJZuY3/nEdowUyuyTduCr3SFCPkacKQHzTj+ZEeAa34zH8sSWDhf8Hd/pmwEY0dQyOG6v2wzAAM5KfhLFo2CcLg2qiHlWPybZD0oxYivPxBc4bNl6HAYiAT8xGeruJ945kD8U6xA6ai/cG/UwGcBJe/I8atgnePfAGvsfh+P1v5ckA7kkus2/dOdwkikLZ+JyewCI8UAUgWGFs2fMLnXWlHtTlneyLv3xMrsAvuBWXdxVBod27cDr2q6rAdzm2Lip01JV63OCC9G1XBSDK8yVO7SqCQrt3IEjlXlUAbkoytXfHnGdcHDFC41Eg7h1De+BIvInrcOW4XjrSC9b7fN5H4v4xFED8GCRqAc5IZthRPI3M7oSN2BEHDY74YZt45xSOTl+Ohxq5al84NvAjycsiqVGFiVNF5qIHHkfcVYOf34nXssEntmD7sU5YDFYa1PpcrMxbYDzVxBPMP84oOh1XvFW4Im9IHcZbaTrYbyTwslxg/xKsc6HZKp87ZuX4CmBdn3jk+jRfKj4Z5awOgK6DLbLfAyhKXwvKfQVaSGKRib4CRelrQbmvQAtJLDIx5SvwJ7W1hTF7nK+PAAAAAElFTkSuQmCC",
            "payment_card": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAAtFJREFUaEPtmEnITmEUx38fEjKPkWFDIkrEgtgoloayQJZWkh02PqxEiQU7KxtZSCSZF6ZSlFJCGTIl85AxU/86V/e73fve577Pvc/r7bunvr7enjP9zzn3POc8HbQ5dbS5/9QAWp3BOgN1BjwjUJeQZwC9xbtNBoYD4yHYvfETeAh8zEtRXgZmA7uABUCPPGUln/8AjgMbDUyq+kYAlgOHgN4lO1ZU3VtgEXAjTTALwATgNtDPhB4DF4EvRa03yT8YWAgMM/lHwFTga1JfFoC9wAZjPgasTBNu0jlXsRHAGWCGCawFDrgCuAVMA/4AY4AXrlZL5lMWzplOlfMqVwBvgKHAZ2BfyU4VUdcnVglXgXmuANTGehaxFID3FTDSFcDvgD3fFfsHQB93F8r6iCMA+r/Y1UIFfCrjw6a3KQC/gF4VOOaqcjTwvFsDUBs97xquCvg0BWiMERUqIZVO6NknD38hALqy1YP/J7oPTHTtQq9tDnkGTG8hiv6A5jDRpVg5/XMpq41GAJ7YHiCBscCoGBjd0nfs96BEdHQR6uy7TbNTEt3sAfDOITADYjuBF4ClwJGU72I3sAfQ7DQk4dBNYCZwGZibOPtkQ5qANKLSAHQC21MsXQC2AFdSzhR9jcMaBFUKSdKMfzYUAJXIZhvwIpvamPZbqay36TU6U/s9YX9ydFkie3ctc+ILkgGHcq2EpekS0uSnRf4pMK4S19yUDrQLrHAXugdMAnShqXzUcVpBs4DrZvgooD29C2W10YPAGuPcafUfGoD2EXW+JWZ4k72QOAHQc8q12E5wEjgNfAuEQqWzAphj9tR2dQu/dM2A+LYC2wI53MiMynh1bC9wykDEpJeAHbHnjdB4dNGtA05lGc57mZNcX2A+MDn2TlQ1kPf2LqVFXhnIJBcAVTvrpb8G4BW+EoTrDJQQRC8VdQa8wleCcJ2BEoLopaLtM/AXFvGIMXSiCHgAAAAASUVORK5CYII=",
            "brad": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAABE9JREFUaEPtmWuoVkUUhh9LTC1vkZeUvKJIiYhdUBN/aKj4I5NCvCFiHBA54AUFNco/ZqWmmIh4SQ2S/vQjQ7yAUpGZZHhDJU2y0lIMIzMtT56UV2bDuPu+b9bss/cnggsOB86s9c5698ysedecRtzj1ugez5/7BBqwgg8DLwLPAwOADsCjwH/AOeBHYBuwFThbbp67sQJK9A1gItDS8AHqgc3AQuCXtH+1CdQAS4FWhsTTLleAScCn/kC1CGieJcCcDIn7Idpes4D3kj9Wi8BMYEUDk0/CRWJMshLVINADOAE0yYmAYLSdegO/hgh0BtYAy9yyvQ1siUzkXWB2ZIzFfQNQEyKgSvGhh/ZnhgN4DHjKklGkj6pT13IEHnKlTnu3eQr4D+AwsB74GKgLTHy1BEZkrmXda0sRUIlTqRpimOU0MBn4uoJvkQS2pwk86G6/kYbkE5cbwAJX30uFXQDaR+DFuJ5ME6gFVsUgeL4i8VaJ2FNAz4yYobArPgHt9R+8r6WEdGHMAN4MIbnx6a5q+e7fAk8b42Pd6nwCL7tDmYC0AP4C9FvVx2J/A/2B7zznncAIS3AGn4s+gU3AFA/kNW8FFkWAf+MUps6G7AN30CMgzK77fAKHgH7m0MqO04C1zkUaaG5OuGmYd3wC550mz2OunwFJCK2CBJwUaN52E+hTFAElK8H1CRBb2dTE7AWGAsMrsF4JzPQJPAaMd0F9XTXSjXwNuA60ifyE6qReArSdpKcsprP2uuf4CrA4VYZ18yv5+UB9SAtJQSZSoRewG3jCkgmgG1gfRU2IZEfIfgc6Af+UcNQH7eYwjwC/JT4hAmksCTsJPKsNA6RoVeFCth8YGHJKj4uA5INu33Fw+5VCZVATSqglpVBxuuik67tETDIP0JddZ4g5A3Q3+N3hooRVOlVC0/YTIM39JdDW7U0tZYx9BBwtIzFK4fQBjsdMkF6B2IMamksq9auIXngXECMk//ew1dpVIXVeOjQNNb3niMTYCKAJgFbOZOUO8SNOwEmcNTYhlXa6DHwPPBOBcQl4ErhoiQlVId2m0kdqbiSJtcWaWoCdz79OEMZuTb1gmProEAE/1xfc69jgCAJZXXV5dvXrfTkgCwH56FVCD0oW/6xJp+N8QVgW05JQno9SMeR2AKNCASECGldP2y4EVMC46WILEXhcr18FJGeBlCZqFnIMEVA5VSl8IARUwLj6k44h3BABxRfZlFfK7wDwXB4EpgLvh4AKGN8IvBrCtayA1KpWIa9+OZRTMq4KpEpU0SwEBPCsU6Xq0KphB538UN+bCwGB6N9DFl0fmjM0rk5ukJPhId/om1WvddZXuuDkJRwk5NQHf24NrrSFVELVqY3O0NBb5/f9vgBUMPS8abZKBFYDktNFmi4rPRQsBz7LMlElAtLjaiUbauqr9T8t/ag/1mu1ftR773HPNpnnsFahzBMUHXifQNFfOIR/C9prt5B9bZVmAAAAAElFTkSuQmCC"
}



def graph_pyvis_network(nodes, edges, directed=False, out_file="pyvis_output.html", nbdisplay=False, filter_menu=False, toggle_physics=True, buttons=[''], width=1800, height=1000, debug=False):
    """{"name": "graph_pyvis_network", 
         "desc": "Take a list of nodes and a list of edges and graph them with pyvis.",
         "return": "In addition to the html file with the pyvis output, also return a pyvis object", 
         "examples": [["mypyvis = graph_pyvis_network(nodes, edges)", "Graph nodes and edges"]
         ], 
         "args": [{"name": "nodes", "default": "None", "required": "True", "type": "list", "desc": "List of nodes with any sort of node formating"},
                  {"name": "edges", "default": "None", "required": "True", "type": "list", "desc": "List of edges with any sort of edge formating"},
                  {"name": "directed", "default": "False", "required": "False", "type": "boolean", "desc": "Show arrows on edges to show direction"},
                  {"name": "out_file", "default": "pyvis_output.html", "required": "False", "type": "string", "desc": "Default filename of the output. Will automatically overwrite and be stored in the same directory as the notebook"},
                  {"name": "nbdisplay", "default": "False", "required": "False", "type": "boolean", "desc": "Display in Notebook as well as write to html file"},
                  {"name": "filter_menu", "default": "False", "required": "False", "type": "boolean", "desc": "Not really sure yet"},
                  {"name": "toggle_physics", "default": "True", "required": "False", "type": "boolean", "desc": "When opoening HTML (in browser or notebook) should physicas automatically be calculated. Takes a lot of time on big graphs"},
                  {"name": "buttons", "default": "['']", "required": "False", "type": "list", "desc": "List of widgets to add to the html output. We've seen physics as the most common"},
                  {"name": "width", "default": "1800", "required": "False", "type": "integer", "desc": "Number of pixels to use as the width for the graph"},
                  {"name": "height", "default": "1000", "required": "False", "type": "integer", "desc": "Number of pixels to use as the height for the graph"},
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Enable debug messages"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "",
         "limitations": ["Formatting happens outside of this function. "]
         }
    """ 

#mynet = Network(height="1000px", bgcolor="#222222", font_color="white", filter_menu=True, notebook=True)

    str_width = f"{width}px"
    str_height = f"{height}px"

    print(f"Graphing Network with {len(nodes)} nodes and {len(edges)} edges")
#    buttons = ['nodes', 'edges', 'physics', 'layout', 'interaction', 'manipulation', 
    out_dir = os.getcwd()

    mynet = pyvis.network.Network(width=str_width, height=str_height, directed=directed, filter_menu=filter_menu, notebook=False)
    for n in nodes:
        try:
            mynet.add_node(n['id'], **n)
        except:
            print(n)
    #mynet.add_node(k, label=v['label'], color=v['color'], title=v['title'])
    for e in edges:
        tedge = e.copy()
        tfrom = tedge['from']
        tto = tedge['to']
        del tedge['from']
        del tedge['to']
        del tedge['id']
        mynet.add_edge(tfrom, tto, **tedge)
    mynet.toggle_physics(toggle_physics)
    mynet.show_buttons(filter_=buttons)
    full_path = f"{out_dir}\\{out_file}"
    mynet.save_graph(out_file)
    #mynet.generate_html(name=out_file, local=False, notebook=True)
#    mynet.show(out_file, local=False)
    print(f"Output to {full_path}")
    if nbdisplay:
        display(IFrame(out_file, width=width+200, height=height+200))
    return mynet

def node_or_edge_format(srcnodeoredge, format_map=None, default_node_format={"color": "#000000", "size": 30, "shape":"dot"}, default_edge_format={"color": "#000000"}, first_hit=True, always_use_default=False, matchlen=3, debug=False):
    """{"name": "node_or_edge_format", 
         "desc": "Provide a method to format nodes and edges based on string matching of the id",
         "return": "A node or edge dictionary with the formatting added if needed", 
         "examples": [["col_dict = ret_bank_cols()", "Returns Zelle Bank to Color List by default"]
         ], 
         "args": [{"name": "nodeoredge", "default": "", "required": "True", "type": "dict", "desc": "Dictionary of a node or edge. Must have an id column at a minimum"},
                  {"name": "format_map", "default": "None", "required": "False", "type": "dict or None", "desc": "Dictionary that has a key of a match string and value of a format dictionary. If None, nothing is added to the node"},
                  {"name": "default_node_format", "default": "{'color': 'Black', 'size': 30, 'shape':'dot'}", "required": "False", "type": "dict", "desc": "If a match occurs, and a certain item is not included this is the default for a node"},
                  {"name": "default_edge_format", "default": "{'color': 'Black'}", "required": "False", "type": "dict", "desc": "If a match occurs, and a certain item is not included this is the default for a edge"},
                  {"name": "first_hit", "default": "True", "required": "False", "type": "Bool", "desc": "Uses the first hit in a format_map. If False, uses the last hit in the format map"},
                  {"name": "always_use_default", "default": "False", "required": "False", "type": "Bool", "desc": "If there is not a hit on the format_map, still use the node or edge defaults. Defaults to False which just returns the node with no formating added."},
                  {"name": "matchlen", "default": "3", "required": "False", "type": "integer", "desc": "How much of the ID we should check against the format map"},
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Enable debug messages"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "",
         "limitations": [""]
         }
    """
    nodeoredge = srcnodeoredge.copy()
    if format_map is None:
        return nodeoredge # If no dict is provided, don't even add the defaults

    if "source" in nodeoredge:
        format_type = "edge"
    else:
        format_type = "node"
    fullid = nodeoredge['id']
    matchid = fullid[0:matchlen]
    format_dict = None
    if format_type == "edge":
        format_dict = default_edge_format.copy()
    else:
        format_dict = default_node_format.copy()
    hit_dict = format_dict
    for m in format_map.keys():
        if debug:
            print(f"ID: {fullid}")
            print(f"Match ID: {matchid}")
            print(f"Match Key: {m}")
        if m[0] == "~":
            full_match = m.replace("~", "")
            if fullid.find(full_match) >= 0:
                hit_dict = format_map[m].copy()
                if first_hit:
                    break
        elif m.find(matchid) >= 0:
            hit_dict = format_map[m].copy()
            if first_hit:
                break
    if hit_dict is not None:
        format_dict.update(hit_dict)
        nodeoredge.update(format_dict)
    else:
        if always_use_default:
            nodeoredge.update(format_dict)
    return nodeoredge


def add_transparency_from_png(b64encoded_in):
    """{"name": "add_transparency_from_png",
         "desc": "Take a PNG with a solid background and make it transparent ",
         "return": "The same base64 encoded PNG (with our without the data tag for IMG tags) with a transparent background",
         "examples": [["trans_b64_png = add_transparency_from_png(b64_png)", "Add transparency"]
         ],
         "args": [{"name": "b64encoded_in", "default": "None", "required": "True", "type": "string", "desc": "Base64 encoded PNG file with a background"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "",
         "limitations": ["Can happen with or without the data prefix for image tags"]
         }
    """


    data_pre = False
    if b64encoded_in.find("data:image/png;base64,") == 0:
        b64encoded_in = b64encoded_in.replace("data:image/png;base64,", "")
        data_pre = True
    srcimage = pil_Image.open(io.BytesIO(base64.b64decode(b64encoded_in)))
    srcimage = srcimage.convert("RGBA")
    newimage = pil_Image.new('RGB', srcimage.size, (255,255,255))
    newimage.paste(srcimage, (0, 0), mask=srcimage)
    thresh = 200
    thres_fn = lambda x : 255 if x > thresh else 0
    new_bw = newimage.convert('L').point(thres_fn, mode='1')

    with io.BytesIO() as output:
        new_bw.save(output, format='PNG')
        png_out = output.getvalue()
    b64_out = base64.b64encode(png_out)
    retval = str(b64_out, 'utf-8')
    if data_pre:
        retval = f"data:image/png;base64,{retval}"

    return retval


def change_png_color(b64_black_png, color):
    """{"name": "change_png_color", 
         "desc": "Take a PNG with a solid black color and change the color to the specified color ",
         "return": "The same base64 encoded PNG in a different color", 
         "examples": [["red_png_b64 = change_png_color(black_png_b64, "red")", "Change the color to red"]
         ], 
         "args": [{"name": "b64_black_png", "default": "None", "required": "True", "type": "string", "desc": "Base64 encoded PNG file with a backgroung"},
                  {"name": "color", "default": "None", "required": "True", "type": "string", "desc": "Color to change to"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "",
         "limitations": ["Color must be in allowed colors list"]
         }
    """ 


    data_pre = False
    if b64_black_png.find("data:image/png;base64,") == 0:
        b64_black_png = b64_black_png.replace("data:image/png;base64,", "")
        data_pre = True
    srcimage = pil_Image.open(io.BytesIO(base64.b64decode(b64_black_png)))
    srcimage = srcimage.convert("RGBA")
    srcpixels = srcimage.load()

    try:
        color_tup = getcolor(color, 'strtup')
        splitrgb = color_tup.strip().split(",")
        if len(splitrgb) == 3:
            nr = int(splitrgb[0])
            ng = int(splitrgb[1])
            nb = int(splitrgb[2])
        else:
            print("bad color")
            nr = 0
            ng = 0
            nb = 0
    except:
        print("there is no try")
        nr = 0
        ng = 0
        nb = 0
    width, height = srcimage.size
    black_max = 20
    black_enough = 20
    for x in range(width):
        for y in range(height):
            r, g, b, a = srcpixels[x, y]
            if not (r == 255 and g == 255 and b == 255):
                if r == g == b == 0:
                    srcpixels[x, y] = (nr, ng, nb, a)
    with io.BytesIO() as output:
        srcimage.save(output, format='PNG')
        png_out = output.getvalue()
    ret_val = str(base64.b64encode(png_out), 'utf-8')

    if data_pre:
        ret_val = f"data:image/png;base64,{ret_val}"

    return ret_val

def display_icon_colors(icons, colors=['black', 'red', 'green', 'blue']):
    """{"name": "display_icon_colors", 
         "desc": "Take a dict of icons and show them displayed in the provided colors (or use all to see all colors)",
         "return": "None - It displays in a notebook", 
         "examples": [["display_icon_colors(pyvis_icons, ['all'])", "Show all Pyvis Icons"]
         ], 
         "args": [{"name": "icons", "default": "None", "required": "True", "type": "dict", "desc": "A dict with keys as names and values as b64encoded PNGs"},
                  {"name": "colors", "default": "None", "required": "True", "type": "list", "desc": "A list of colors" }
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "",
         "limitations": ["All is more like 'most']
         }
    """ 
    if colors[0] == 'all':
        colors = ['red', 'darkred', 
                  'maroon', 'springgreen', 'green', 'darkgreen', 
                  'blue', 'darkblue',  
                  'pink', 'deeppink', 'magenta',
                  'purple', 'cyan', 
                  'coral', 'orange', 
                  'yellow', 'gold',
                  'brown', 'gray', 'black']

    out_html = f"<H1>Icons Defined: {len(icons)}</H1>\n"
    out_html += "<TABLE>\n"
    out_html += "<TH><TD>Original</TD><TD>Transparency Fix</TD>"
    for c in colors:
        out_html += f"<TD>{c}</TD>"
    out_html += "</TH>\n"
    for k, v in icons.items():
        out_html += f"<TR><TD>{k}</TD>\n"
        out_html += f"<TD><img src='{v}'></TD>\n"
        out_html += f"<TD><img src='{add_transparency_from_png(v)}'></TD>\n"
        for c in colors: 
            out_html += f"<TD><img src='{change_png_color(add_transparency_from_png(v), c)}'></TD>\n"
        out_html += "</TR>"
    out_html += "</TABLE>"
    display(HTML(out_html))

def getcolor(incolor, myformat):
    """{"name": "getcolor", 
         "desc": "Take a color and return it in a specific format",
         "return": "The color represented by the requested format", 
         "examples": [["red_html = getcolor('red', "html")", "Red represented has Hex for HTML"],
                      ["green_strtup = getcolor('green', "strtup")", "Green as a RGB String tuple like 0,255,0"]
         ],
         "args": [{"name": "incolor", "default": "None", "required": "True", "type": "string", "desc": "Name of the color"},
                  {"name": "myformat", "default": "None", "required": "True", "type": "string", "desc": "html or strtup"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "",
         "limitations": ["Color must be in allowed colors list"]
         }
    """

    allowed_colors = [
    'black',
    'blue', 
    'lightblue', # JPM
    'darkblue',
    'gray',
    'green', #Wells
    'darkgreen',
    'springgreen'
    'lavender', # BBT
    'purple', #Citi
    'maroon',
    'red', #BAC
    'darkred',
    'coral',
    'orange',
    'white',
    'brown',
    'peachpuff', #USB
    'yellow',
    'gold', #PNC
    'pink',
    'deeppink',
    'magenta',
    'cyan', # H50
    'honeydew' # Ally
    ]

    if incolor.lower() not in allowed_colors:
        print(f"{incolor} not in allowed_colors")
        print(f"{allowed_colors}")
        return ""
    c = colour.Color(incolor)
    if myformat == "html":
        return c.hex_l.upper()
    elif myformat == "strtup":
        html_l = c.hex_l.upper()
        red = html_l[1:3]
        green = html_l[3:5]
        blue = html_l[5:7]
        outstr = f"{int(red, 16)},{int(green,16)},{int(blue, 16)}"
        return outstr


